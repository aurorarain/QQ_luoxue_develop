"""Download pinned public sources for review/reproduction; never executes upstream code."""
import io
import json
from pathlib import Path,PurePosixPath
import sys
from urllib.request import urlopen,Request
import zipfile


def download(destination):
    manifest=Path(__file__).resolve().parents[1]/'deploy/reviewed-plugins.json'
    for row in json.loads(manifest.read_text(encoding='utf-8')):
        repo,sha=row['repo'],row['sha']
        request=Request(f'https://codeload.github.com/{repo}/zip/{sha}',headers={'User-Agent':'luoxue-plugin-backup'})
        with urlopen(request,timeout=120) as response:
            archive=zipfile.ZipFile(io.BytesIO(response.read()))
        prefix=PurePosixPath(archive.namelist()[0])
        root=Path(destination)/repo.split('/')[1];root.mkdir(parents=True,exist_ok=True)
        for item in archive.infolist():
            relative=PurePosixPath(item.filename).relative_to(prefix)
            if '..' in relative.parts:raise ValueError('unsafe archive path')
            path=root.joinpath(*relative.parts)
            if item.is_dir():path.mkdir(parents=True,exist_ok=True)
            else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(item))
        (root/'UPSTREAM_REVIEW.json').write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
        print('DOWNLOADED',repo,sha)


if __name__=='__main__':download(sys.argv[1])
