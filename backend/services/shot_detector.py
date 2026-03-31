import os
import shutil
import subprocess
import tempfile
from backend.models import Shot
from scenedetect import detect, ContentDetector

def detect_shots(job_id: str, video_path: str) -> list[Shot]:
    """
    1. PySceneDetect 场景检测
    2. FFmpeg 关键帧提取
    3. 兜底处理
    4. 产生 Shot 列表并返回
    """
    # 步骤 1 — 场景检测
    scene_list = detect(video_path, ContentDetector(threshold=27.0))
    
    def get_video_duration(path: str) -> float:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", path]
        try:
            return float(subprocess.check_output(cmd).decode().strip())
        except FileNotFoundError:
            raise RuntimeError("系统未找到 ffprobe。请确保 FFmpeg 已安装并添加到系统环境变量 PATH 中。")
        except Exception:
            return 0.0

    duration = get_video_duration(video_path)
    shots_data = []

    if scene_list:
        for scene in scene_list:
            start = scene[0].get_seconds()
            end = scene[1].get_seconds()
            shots_data.append((start, end))

    # 步骤 3 — 兜底处理：如果检测到的镜头少于 3 个，强制按每 30 秒切一个镜头
    if len(shots_data) < 3 and duration > 0:
        shots_data = []
        interval = 30.0
        current_time = 0.0
        while current_time < duration:
            end_time = min(current_time + interval, duration)
            shots_data.append((current_time, end_time))
            current_time = end_time

    if not shots_data:
        shots_data = [(0.0, duration)]

    # Use system temp directory
    temp_root = os.path.join(tempfile.gettempdir(), "filmlens")
    frames_dir = os.path.join(temp_root, job_id, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    # 假设 static 目录在当前工作目录(backend)下
    static_frames_dir = f"static/jobs/{job_id}/frames"
    os.makedirs(static_frames_dir, exist_ok=True)

    result_shots = []

    # 步骤 2 & 4 — 关键帧提取与保存
    total_shots = len(shots_data)
    print(f"[ShotDetector] Starting keyframe extraction for {total_shots} shots...")
    for i, (start_time, end_time) in enumerate(shots_data):
        shot_id = i + 1
        if shot_id % 5 == 0 or shot_id == 1 or shot_id == total_shots:
            print(f"[ShotDetector] Processing shot {shot_id}/{total_shots}...")
        shot_duration = end_time - start_time
        
        # start_time + (duration * 0.35) 处的帧作为关键帧
        keyframe_time = start_time + (shot_duration * 0.35)
        keyframe_path = os.path.join(frames_dir, f"shot_{shot_id:04d}.jpg")
        
        # FFmpeg 命令提取并压缩到最大宽度 960px
        ff_cmd = [
            "ffmpeg", "-y", "-ss", f"{keyframe_time:.3f}", "-i", video_path,
            "-vf", "scale='min(960,iw)':-1",
            "-frames:v", "1", "-q:v", "2", keyframe_path
        ]
        try:
            subprocess.run(ff_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except FileNotFoundError:
            raise RuntimeError("系统未找到 ffmpeg。请确保 FFmpeg 已安装并添加到系统环境变量 PATH 中。")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e}")
        
        # 同时复制一份到 /static/jobs/{job_id}/frames/
        static_keyframe_path = os.path.join(static_frames_dir, f"shot_{shot_id:04d}.jpg")
        if os.path.exists(keyframe_path):
            shutil.copy2(keyframe_path, static_keyframe_path)
        
        keyframe_url = f"/static/jobs/{job_id}/frames/shot_{shot_id:04d}.jpg"
        
        result_shots.append(Shot(
            shot_id=shot_id,
            start_time=start_time,
            end_time=end_time,
            duration=shot_duration,
            keyframe_path=keyframe_path,
            keyframe_url=keyframe_url
        ))

    return result_shots
