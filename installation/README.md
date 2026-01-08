# stella_vslam 설치 가이드

Ubuntu 22.04 환경에서 stella_vslam을 처음부터 설치하는 방법을 안내합니다.

---

## 시스템 요구사항

- **OS**: Ubuntu 22.04 LTS
- **RAM**: 8GB 이상 권장
- **Disk**: 10GB 이상 여유 공간

---

## 1. 필수 패키지 설치

```bash
sudo apt update
sudo apt install -y build-essential cmake git pkg-config \
    libeigen3-dev libyaml-cpp-dev libopencv-dev \
    libg2o-dev libgoogle-glog-dev libgflags-dev \
    libatlas-base-dev libsuitesparse-dev
```

---

## 2. Pangolin 설치 (시각화 라이브러리)

```bash
cd ~/
git clone https://github.com/stevenlovegrove/Pangolin.git
cd Pangolin
git checkout v0.8
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
```

---

## 3. FBoW 설치 (Bag of Words 라이브러리)

```bash
cd ~/
git clone https://github.com/stella-cv/fbow.git
cd fbow
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
```

---

## 4. stella_vslam 본체 설치

```bash
cd ~/
git clone https://github.com/stella-cv/stella_vslam.git
cd stella_vslam
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_VIEWER=ON
make -j$(nproc)
sudo make install
```

---

## 5. stella_vslam_examples 빌드

```bash
cd ~/
git clone https://github.com/stella-cv/stella_vslam_examples.git
cd stella_vslam_examples
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

빌드가 완료되면 `~/stella_vslam_examples/build/` 디렉토리에 다음 실행 파일들이 생성됩니다:
- `run_video_slam`: 비디오로부터 SLAM 실행
- `run_slam_localization`: 기존 맵으로 위치 추정

---

## 6. ORB 어휘 파일 다운로드

```bash
cd ~/stella_vslam_examples
mkdir -p data
cd data
wget https://github.com/stella-cv/FBoW_orb_vocab/raw/main/orb_vocab.fbow
```

---

## 7. 설치 확인

```bash
cd ~/stella_vslam_examples/build
./run_video_slam --help
```

도움말이 정상적으로 출력되면 설치가 완료된 것입니다.

---

## 8. Python 바인딩 설치 (선택 사항)

키프레임 데이터 추출을 위해 Python 바인딩이 필요합니다.

```bash
cd ~/
git clone https://github.com/stella-cv/StellaVSLAM-Python-bindings.git
cd StellaVSLAM-Python-bindings
pip3 install -r requirements.txt
pip3 install .
```

---

## 문제 해결

### 1. CMake 버전 오류
```bash
# CMake 최신 버전 설치
sudo apt remove cmake
sudo snap install cmake --classic
```

### 2. OpenCV 버전 충돌
```bash
# OpenCV 4.x 설치
sudo apt install libopencv-dev python3-opencv
```

### 3. Pangolin 빌드 오류
```bash
# 추가 의존성 설치
sudo apt install libglew-dev libpython3-dev
```

---

## 참고 자료

- [stella_vslam 공식 GitHub](https://github.com/stella-cv/stella_vslam)
- [stella_vslam_examples](https://github.com/stella-cv/stella_vslam_examples)
- [FBoW 어휘 파일](https://github.com/stella-cv/FBoW_orb_vocab)
