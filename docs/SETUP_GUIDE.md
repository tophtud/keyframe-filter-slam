# 개발 환경 설정 및 재현 가이드

이 문서는 `vslam-keyframe-filter` 프로젝트를 재현하고 개발하기 위한 전체 과정을 안내합니다.

---

## 1. GitHub에 업로드할 파일 목록

사용자님의 명령어 기록을 분석한 결과, 우리 프로젝트의 재현과 분석에 필수적인 스크립트와 설정 파일은 다음과 같습니다. 이 파일들을 `keyframe-filter-slam` 저장소에 업로드해야 합니다.

### 1.1. 핵심 Python 스크립트 (`src/` 디렉토리에 저장)

- **`extract_keyframes.py`**: `map.msg` 파일에서 키프레임의 위치, 자세, 이미지 데이터를 추출하는 스크립트입니다. (기존 `extract_keyframes_aist_living_lab_2.py`)
- **`generate_waypoints.py`**: 세미-오토매틱 웨이포인트 생성 로직이 담길 스크립트입니다. (기존 `generate_waypints_spatial_1.py` 등)
- **`visualize_coverage.py`**: 선택된 웨이포인트의 랜드마크 커버리지를 시각화하는 스크립트입니다. (기존 `visualize_coverage_final.py`)
- **`filter.py`**: 위치, 방향, 품질을 종합 평가하는 메인 필터링 로직이 담길 스크립트입니다. (신규 작성)

### 1.2. `stella_vslam` 설정 파일 (`config/` 디렉토리 생성 후 저장)

- **`insta360_x3_stella_vslam.yaml`**: Insta360 카메라용 설정 파일입니다.
- **`equirectangular.yaml`**: Equirectangular (360도) 이미지 공통 설정 파일입니다.

### 1.3. 데이터 파일 (`data/` 디렉토리에 저장)

- **`kyw_3_map.msg` (샘플)**: 테스트 및 재현을 위한 샘플 `map.msg` 파일 1개. (용량이 크므로 전체 데이터는 별도 관리)
- **`orb_vocab.fbow`**: SLAM에 사용되는 어휘 파일. (다운로드 링크를 README에 명시)

> **참고:** `video.mp4` 같은 원본 비디오 파일은 용량이 매우 크므로 Git 저장소에 포함하지 않고, 별도로 관리하거나 다운로드 링크를 제공하는 것이 좋습니다.

---

## 2. `stella_vslam` 설치 가이드 (Ubuntu 22.04 기준)

`stella_vslam`을 처음부터 설치하고 빌드하는 과정입니다.

### 2.1. 필수 패키지 설치

```bash
sudo apt update
sudo apt install -y build-essential cmake git pkg-config libeigen3-dev libyaml-cpp-dev libg2o-dev libgoogle-glog-dev libgflags-dev libatlas-base-dev libsuitesparse-dev
```

### 2.2. `pangolin` (시각화 라이브러리) 설치

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

### 2.3. `stella_vslam` 및 의존성 라이브러리 설치

```bash
cd ~/
mkdir -p stella_vslam_libs && cd stella_vslam_libs

# fbow (필수)
git clone https://github.com/stella-cv/fbow.git
cd fbow
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
cd ../..

# stella_vslam_viewer (선택 사항, 시각화용)
git clone https://github.com/stella-cv/stella_vslam_viewer.git
cd stella_vslam_viewer
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
cd ../..
```

### 2.4. `stella_vslam` 본체 설치

```bash
cd ~/
git clone https://github.com/stella-cv/stella_vslam.git
cd stella_vslam
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_VIEWER=ON
make -j$(nproc)
sudo make install
```

### 2.5. `stella_vslam_examples` 빌드 (실행 파일 생성)

사용자님의 명령어 기록을 보면 `stella_vslam_examples`를 사용하셨습니다. 이 프로젝트를 빌드해야 `run_video_slam` 같은 실행 파일이 생성됩니다.

```bash
cd ~/
git clone https://github.com/stella-cv/stella_vslam_examples.git
cd stella_vslam_examples
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

이제 `~/stella_vslam_examples/build/` 디렉토리 안에 `run_video_slam` 등의 실행 파일이 생성되어, 제공해주신 명령어들을 실행할 수 있습니다.

---

이 가이드 문서를 `keyframe-filter-slam` 저장소의 `docs/` 폴더에 `SETUP_GUIDE.md` 파일로 저장했습니다. 이제 이 목록에 따라 기존에 작성하신 스크립트 파일들을 업로드하고, 신규 코드를 작성해 나가면 됩니다.
