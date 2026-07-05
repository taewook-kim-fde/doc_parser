#!/usr/bin/env python3
"""
이미지를 config 보존한 채 단일 레이어로 flatten 한다.
docker export|import 로 최종 병합 fs만 재생성 → 하위 레이어의 purge 잔재(perl-base 등)
까지 제거되어 레이어 스캐너(Labrador)에도 검출되지 않는다.

사용: flatten_image.py <src_image> [dst_image]   # dst 생략 시 src 덮어씀
"""
import json
import subprocess
import sys


def sh(*args):
    return subprocess.run(
        args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    ).stdout.strip()


def build_changes(cfg):
    changes = []
    for e in cfg.get("Env") or []:
        changes += ["--change", f"ENV {e}"]
    if cfg.get("WorkingDir"):
        changes += ["--change", f"WORKDIR {cfg['WorkingDir']}"]
    if cfg.get("User"):
        changes += ["--change", f"USER {cfg['User']}"]
    for port in (cfg.get("ExposedPorts") or {}):
        changes += ["--change", f"EXPOSE {port}"]
    for k, v in (cfg.get("Labels") or {}).items():
        changes += ["--change", f'LABEL {k}={json.dumps(v)}']
    # ENTRYPOINT / CMD 는 exec(JSON 배열) 형식으로 보존
    if cfg.get("Entrypoint"):
        changes += ["--change", f"ENTRYPOINT {json.dumps(cfg['Entrypoint'])}"]
    if cfg.get("Cmd"):
        changes += ["--change", f"CMD {json.dumps(cfg['Cmd'])}"]
    return changes


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: flatten_image.py <src_image> [dst_image]")
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src

    inspect = json.loads(sh("docker", "inspect", src))[0]
    cfg = inspect.get("Config", {})
    changes = build_changes(cfg)

    cid = sh("docker", "create", src)
    try:
        # docker export <cid> | docker import [changes] - <dst>
        exporter = subprocess.Popen(["docker", "export", cid], stdout=subprocess.PIPE)
        importer = subprocess.Popen(
            ["docker", "import"] + changes + ["-", dst], stdin=exporter.stdout
        )
        exporter.stdout.close()
        importer.communicate()
        if importer.returncode != 0:
            sys.exit(f"docker import 실패: {dst}")
    finally:
        subprocess.run(
            ["docker", "rm", cid], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    print(f"flattened: {src} -> {dst}")


if __name__ == "__main__":
    main()
