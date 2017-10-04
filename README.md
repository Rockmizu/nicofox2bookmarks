# NicoFox to Firefox Bookmarks #

這個軟體協助您將 NicoFox 列表中的項目匯出並整合至指定的書籤備份檔。

隨著 Firefox 瀏覽器更新，舊的擴充套件架構將被捨棄。鑒於 [NicoFox 的原開發者已宣布停止開發][Stop Develop News]，屆時若無人接手，NicoFox 也將隨之步入歷史。Firefox 57 及其後版本，將無法繼續啟用 NicoFox 擴充套件。如果您仍在意 NicoFox 列表中的項目，本軟體提供一個機會將其轉換為書籤並得以繼續保存。

[Stop Develop News]: https://www.ptt.cc/bbs/Niconico/M.1502551491.A.41D.html "NicoFox 停止開發聲明。"

## 軟體特色 ##

* 完整匯出並保存所有 NicoFox 列表中的項目。
* 支援 GNU gettext 多語言系統，原生支援繁體中文及英文。
* 支援讀取 jsonlz4 壓縮書籤備份檔格式。
* 保持書籤的**加入時間**與該項目實際加入列表的時間一致。
* 允許指定書籤**資料夾名稱**及其**描述**。
* 允許為這些書籤添加指定的**標籤**。
* 提供**命令列**及**圖形使用者介面**兩種使用方式，可依喜好及需求自由選擇。
* 在特定條件下允許**一鍵完成**所有轉換工作。

## 適用對象 ##

適用於裝有 NicoFox 擴充套件，且欲將其列表中之項目加至書籤的使用者。

無論您是經驗老道的軟體工程師還是完全不懂程式設計皆可安心使用。

## 前置需求 ##

* Python 3 執行環境（已於 Python 3.6+ 進行測試）  
  若您不曾安裝過 Python，請至[官方網站][Python Official Site]下載安裝。詳情請[參閱 FAQ][Goto FAQ]。

* lz4 package（Python）（可選）  
  本軟體原生支援壓縮的書籤備份格式（副檔名為 jsonlz4），但此額外函數庫可以大幅提升解壓縮的效率。需要的朋友們可藉由套件管理工具 pip 並於命令列執行下列指令安裝：  
  `pip install lz4`

[Python Official Site]: https://www.python.org/ "Python 官方網站。"
[Goto FAQ]: #FAQ "跳至 FAQ"

## 使用方式 ##

本軟體提供兩種使用方式：*命令列介面*（*CLI*）及*圖形使用者介面*（*GUI*）。

進階的使用者也可透過 Python 程式碼對本軟體直接進行呼叫。

### 命令列介面（Command Line Interface，CLI） ###

nicofox2bookmarks.py 即命令列介面，提供核心功能。使用者必須自己找出相關的檔案路徑，並搭配命令列參數使用。

#### 命令列參數說明： ####

* `-n` 或 `--nicofox`  
  NicoFox 資料庫檔案路徑。
* `-b` 或 `--bookmarks`  
  原始書籤備份檔路徑。
* `-o` 或 `--output`  
  整合書籤備份檔路徑。（輸出檔案）
* `-c` 或 `--container`  
  在選單中建立的書籤資料夾的名稱。
* `-d` 或 `--container-desc`  
  在選單中建立的書籤資料夾的描述。
* `-t` 或 `--common-tags`  
  共同標籤，所有從 NicoFox 匯入的書籤都會被加上這些標籤。（多於一個以逗號分隔）

#### 命令列使用範例： ####

	nicofox2bookmarks.py -n smilefox.sqlite -b bookmarks-2112-09-03.json -o nicofox-bookmarks.json -c "My Niconico" -t NicoFox,Niconico,Video

其中，

* *smilefox.sqlite* 是 NicoFox 儲存列表的資料庫檔案。
* *bookmarks-2112-09-03.json* 是 Firefox 書籤備份檔。
* *nicofox-bookmarks.json* 是轉換後輸出的檔案名稱。
* *My Niconico* 是建立的書籤資料夾名稱。
* *NicoFox*、*Niconico* 及 *Video* 是加在書籤上的標籤。
* 由於這裡沒有指定「資料夾描述」，因此會採用預設的描述。關於預設值細節請參閱 FAQ。

其作用可以簡單理解為：將 *smilefox.sqlite* 內容與 *bookmarks-2112-09-03.json* 合併的結果存至 *nicofox-bookmarks.json*。

隨後將 *nicofox-bookmarks.json* 匯入 Firefox 收藏庫即可完成。

### 圖形使用者介面（Graphic User Interface，GUI） ###

nicofox2bookmarks_gui.py 即圖形使用者介面，直接執行即可開啟 GUI。此 GUI 的使用方式與命令列大同小異，很容易可以發現，表單上的項目幾乎一一對應至命令列參數。

除此之外，GUI 也提供了相對自動的功能，可讀取並列出 Firefox 使用者設定檔。當執行匯出及整合時，會依據目前所選取的使用者設定檔來填補表單留空部分。關於自動填空的細節請[參閱 FAQ][Goto FAQ]。

## 注意事項 ##

本軟體所產生的書籤備份檔皆省略了 GUID 屬性。若有長期保存該備份的需求，建議將其匯入 Firefox，**確認無誤之後**，再用 Firefox 本身的功能匯出一次。

## FAQ ##

### Q1：我需要付費購買這個軟體嗎？ ###
這個軟體是**完全免費**的！且**開放原始碼**，任何人皆可自由使用並檢視本軟體的內容。  
若您發現有人向您收取使用本軟體的費用，請務必**不要**付錢。

### Q2：我完全沒有寫過程式，什麼是 Python？我該使用哪個版本？要如何安裝並使用？ ###
Python 是一種高階指令稿程式語言（或通俗地稱腳本程式語言），其擁有大量內建函數庫及支援第三方軟體包，能夠快速設計便利的應用程式。現階段 Python 存在 Python 2 及 Python 3 兩個主要版本，彼此在某些層面上互不相容。

本軟體採用 Python 3 作為撰寫的基礎，如果您沒有安裝過 Python，建議直接到[官方網站][Python Official Site]下載最新版本（註）進行安裝（32 或 64 位元版本皆可）。如果您曾經安裝過 Python，請確認是否為 Python 3。

安裝完畢後，您會發現副檔名為 py 的檔案已經與 Python 直譯器建立關聯。可直接雙擊 py 檔案執行，就如同執行一般應用程式一樣。您也可以從命令列介面，切換到該資料夾，並依前述範例指定參數並執行。

註：本 FAQ 撰寫時間點，官方網站上的最新版本是 Python 3.6.2。

### Q3：我可以在我的程式中使用這些程式碼嗎？ ###
可以的，只要在產品中附上原作者、出處及授權資訊即可。詳細請參閱[授權條款](#授權條款 "跳至授權條款")一節。

### Q4：我要如何找到使用說明中提及的那些檔案？ ###
* NicoFox 資料庫檔案：  
  通常名為 *smilefox.sqlite* 並儲存在 *Firefox 使用者設定檔資料夾*的根目錄。

* Firefox 書籤備份檔：  
  由 Firefox 自身的備份書籤功能即可獲得。以 Firefox 54 為例，點選星號圖示旁的[顯示所有書籤]->[匯入及備份]->[備份]即可。預設檔名是 bookmarks-yyyy-mm-dd.json，其中 yyyy-mm-dd 為備份當天日期。

### Q5：Firefox 的使用者設定檔在哪裡？ ###
打開 Firefox，並在網址列鍵入 `about:profiles` 後前往，找到欲進行轉換之設定檔，點擊「*根目錄*」欄位後的「*開啟資料夾*」。此時打開的即是該 Firefox 使用者設定檔資料夾。

每個使用者設定檔的 NicoFox 資料庫都是獨立的，請選取要進行轉換的使用者設定檔。如果您對使用者設定檔毫無概念且不曾改動過，則選取名為 *default* 的設定檔即可。

### Q6：我沒有（或忘了）指定某某參數，程式仍然執行了？ ###
無論您使用的是命令列還是 GUI，沒有指定的參數都會以預設參數執行。

以命令列介面為例：

* NicoFox 資料庫預設是當前工作目錄下名為 *smilefox.sqlite* 的檔案。
* 原始書籤備份檔預設為當前工作目錄下名為 *bookmarks-yyyy-mm-dd.json* 的檔案。  
  （註：其中 yyyy-mm-dd 為執行當天的西元年、月、日。）
* 輸出檔案預設在當前工作目錄下，檔名為 *bookmarks-output.json*。
* 書籤資料夾名稱預設為 *NicoFox*。
* 書籤資料夾描述預設為 *Bookmarks imported from NicoFox database using NicoFox to Firefox Bookmarks.*。  
  （註：此句會依選取的語言不同而產生變化，若想留空只要指定 `-d ""` 參數即可。）
* 標籤預設值為無，即不會主動為書籤加入任何標籤。

在 GUI 中，當表單中某個項目留空時，會採取與命令列介面相同的預設值。但 GUI 會確認預設值中指定的檔案是否存在，若不存在，則會依序於各目錄中找尋適當的檔案：

* NicoFox 資料庫
  1. 當前工作目錄，名為 *smilefox.sqlite* 的檔案。
  2. 當前所選的使用者設定檔之根目錄，名為 *smilefox.sqlite* 的檔案。

* 原始書籤備份檔（下列 yyyy-mm-dd 將代換為執行當天的西元年、月、日）
  1. 當前工作目錄，名為 *bookmarks-yyyy-mm-dd.json* 的檔案。
  2. 當前所選的使用者設定檔之根目錄，由 Firefox 自動備份之最新的書籤檔案。（註）

* 輸出檔案（與 CLI 預設略不同）  
  當前工作目錄下，命名為 *bookmarks-yyyy-mm-dd-with-nicofox.json*。  
  若該檔案已存在，則會依序在檔名後面遞增追加序號，直到沒有檔名衝突：
  1. bookmarks-yyyy-mm-dd-with-nicofox-2.json
  2. bookmarks-yyyy-mm-dd-with-nicofox-3.json
  3. bookmarks-yyyy-mm-dd-with-nicofox-4.json……依此類推

以上任何檔案搜尋過後，無法找到合適條件者，會中斷並請您進行填寫。

註：GUI 所尋找的自動書籤備份是由 Firefox 進行管理，若您最近曾更動書籤，這個備份很有可能與您現在的書籤不符。強烈建議手動匯出書籤進行指定合併。

### Q7：「*在檔案總管中檢視*」打開了不正確的資料夾。 ###
這是目前一個已知的 bug，作者還在尋找解決方式中，造成不便敬請見諒。

### Q8：我發現 bug 了！該怎麼辦？ ###
歡迎到 GitHub 的 issues 專區發表問題，在提問時請盡可能提供您的系統環境及詳細狀況，這也有助於快速解決您的問題喔！

## 授權條款 ##

本軟體採用 [**MIT 授權條款**](LICENSE)（**MIT License**）。

使用本軟提即表示您同意此授權條款的所有內容。
