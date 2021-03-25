# Python Image Tools for Windows


```sh
main.py -m get-config -i camera-trap-desktop.ini -o std
main.py -m set-config -i camera-trap-desktop.ini -s Folders:foo:foo_path -o std
main.py -m add-folder -d camera-trap.db -f d:\path\to\images
```

## Build


```
$ venv\Scripts\activate.ps1
$ pyinstaller -F main.py -p clam
```
