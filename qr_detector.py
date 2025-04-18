import cv2
import numpy as np
import zxingcpp
from zxingcpp import BarcodeFormat


class QRDetector:
    def __init__(self, camera_matrix, dist_coeffs):
        self.format = BarcodeFormat.DataMatrix
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        # Các tham số cần thiết
        num_QR_points = (2, 2)  # Số lượng điểm trên mã QR mặc định là 4
        self.dist2pts = 15  # Khoảng cách giữa 2 point
        # Chuẩn bị tọa độ thực tế của các tâm vòng tròn trong không gian 3D
        self.objp = np.zeros((np.prod(num_QR_points), 3), np.float32)
        self.objp[:, :2] = np.mgrid[
            0 : num_QR_points[0], 0 : num_QR_points[1]
        ].T.reshape(-1, 2)
        self.objp *= self.dist2pts

    def calculate3DCorners(self, objp, rvec, tvec):
        # Ensure objp is of type float64 (equivalent to CV_64F in C++)
        objp_double = np.asarray(objp, dtype=np.float64)
        # Convert rotation vector to rotation matrix using Rodrigues
        rotation_matrix, _ = cv2.Rodrigues(rvec)
        # Create the homogeneous transformation matrix
        homo_matrix = np.eye(4, dtype=np.float64)
        homo_matrix[:3, :3] = rotation_matrix
        homo_matrix[:3, 3] = tvec.flatten()
        # Add a homogeneous coordinate (1) to objp for matrix multiplication
        ones = np.ones((objp_double.shape[0], 1), dtype=np.float64)
        objp_homo = np.hstack((objp_double, ones))  # Concatenate objp with ones
        # Apply the homogeneous transformation
        corners_3d_camera = (homo_matrix @ objp_homo.T).T
        # Return the 3D coordinates in the camera frame (remove the homogeneous coordinate)
        return corners_3d_camera[:, :3].copy()

    def matching(self, text, x_qc, y_qc):
        y_qc = -y_qc 
        print("---------------------------------------------")
        print(text, "x_qr: ", x_qc, " y_qr: ", y_qc)
        # text = list(text)
        r, c = text[0:2]
        c = int(c) - 1
        r = int(r) - 1
        context = text[2:]
        x_center = 0
        y_center = 0

        if r == 0 and c == 0:
            x_center = -x_qc - 30
            y_center = -y_qc + 30
        elif r == 0 and c == 1:
            x_center = -x_qc - 10
            y_center = -y_qc + 30
        elif r == 0 and c == 2:
            x_center = -x_qc + 10
            y_center = -y_qc + 30
        elif r == 0 and c == 3:
            x_center = -x_qc + 30
            y_center = -y_qc + 30

        elif r == 1 and c == 0:
            x_center = -x_qc - 30
            y_center = -y_qc + 10
        elif r == 1 and c == 1:
            x_center = -x_qc - 10
            y_center = -y_qc + 10
        elif r == 1 and c == 2:
            x_center = -x_qc + 10
            y_center = -y_qc + 10
        elif r == 1 and c == 3:
            x_center = -x_qc + 30
            y_center = -y_qc + 10

        elif r == 2 and c == 0:
            x_center = -x_qc - 30
            y_center = -y_qc - 10
        elif r == 2 and c == 1:
            x_center = -x_qc - 10
            y_center = -y_qc - 10
        elif r == 2 and c == 2:
            x_center = -x_qc + 10
            y_center = -y_qc - 10
        elif r == 2 and c == 3:
            x_center = -x_qc + 30
            y_center = -y_qc - 10

        elif r == 3 and c == 0:
            x_center = -x_qc - 30
            y_center = -y_qc - 30
        elif r == 3 and c == 1:
            x_center = -x_qc - 10
            y_center = -y_qc - 30
        elif r == 3 and c == 2:
            x_center = -x_qc + 10
            y_center = -y_qc - 30
        elif r == 3 and c == 3:
            x_center = -x_qc + 30
            y_center = -y_qc - 30

        print(context, " x_cam: ", x_center, "y_cam: ", y_center)
        return context, x_center, y_center

  
    def detect(self, frame):
        # Đọc mã QR
        barcode = zxingcpp.read_barcode(frame, self.format)
        if not barcode:
            return None

        frame_h, frame_w = frame.shape[:2]  # Lấy kích thước ảnh

        # Lấy các điểm góc của QR code
        positions = np.array(
            [
                [barcode.position.top_left.x, barcode.position.top_left.y],
                [barcode.position.top_right.x, barcode.position.top_right.y],
                [barcode.position.bottom_left.x, barcode.position.bottom_left.y],
                [barcode.position.bottom_right.x, barcode.position.bottom_right.y],
            ],
            dtype=np.float32,
        )

        # === ĐẢO TRỤC (nếu ảnh bị ngược) ===
        # Đảo trục X (trái - phải)
        positions[:, 0] = frame_w - positions[:, 0]

        # Đảo trục Y (trên - dưới) nếu cần
        positions[:, 1] = frame_h - positions[:, 1]

        # Giải PnP
        success, rvec, tvec = cv2.solvePnP(
            self.objp, positions, self.camera_matrix, self.dist_coeffs
        )
        if not success:
            return None

        # Tính góc quay (yaw)
        rotation_matrix, _ = cv2.Rodrigues(rvec)
        yaw_rad = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
        barcode_orientation = - round(np.degrees(yaw_rad) * 5) / 5  # Làm tròn bội số 0.2

        # Đảo góc nếu cần (nếu bạn thấy góc bị âm/dương ngược lại)
        # barcode_orientation = -barcode_orientation

        # Tính trung điểm để xác định vị trí
        corners_3d_camera = self.calculate3DCorners(self.objp, rvec, tvec)
        x0, y0 = corners_3d_camera[0][:2]
        x2, y2 = corners_3d_camera[2][:2]
        x3, y3 = corners_3d_camera[3][:2]

        x_center = int((x0 + x3) / 2)
        y_center = int((y0 + y2) / 2)

        # Đảo trục trung điểm nếu cần
        # x_center = -x_center
        # y_center = -y_center

        # Mapping lại theo nội dung mã QR và lưới
        context, x_center_real, y_center_real = self.matching(
            barcode.text, x_center, y_center
        )

        print("Angle: ", barcode_orientation)

        return f"{context} {barcode_orientation} {x_center_real} {y_center_real}"
