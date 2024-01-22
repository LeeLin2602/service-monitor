# Simple Service Monitor

## Config

至 `config` 進行設定，可以將所有 `xxx.sample` 檔案都複製成一份 `xxx`，然後修改裏面內容。

## Utils

至 `utils` 撰寫測試腳本，參數會用 environment 的方式傳入，結果用 exit code 傳出，對應表：
| Code | Message |
| - | - |
| 0 | ok |
| 1 | unknown |
| 2 | warning |
| 3 | danger |
| 4 | error |

## Usage

```
# sudo make build
# sudo make run
# sudo make daemon
# sudo make stop
```
