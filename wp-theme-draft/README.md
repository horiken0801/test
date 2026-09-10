# センター南校ページ 設置手順

## 現状: 一般公開前のプレビューモードです

`parts-centerminami.php` の冒頭にある `$center_minami_preview_only = true;` により、
現在は**管理者としてログインしている人だけ**実際の内容(住所・写真など)が表示され、
それ以外の一般訪問者には住所等を含まない汎用の「準備中」メッセージだけが表示されます。

- 手順自体(カテゴリー作成・`category.php`編集・アップロード)は今のうちに進めてOKです
- 一般公開する準備が整ったら、`parts-centerminami.php` 内の `$center_minami_preview_only` を `false` に変更してください
- あわせて、公開時にはAIOSEOの「センター南校」カテゴリー編集画面で **noindex設定を外す**(現状は特に設定不要ですが、二重の安全策として非公開中は念のためnoindexにしておくことを推奨します)、およびヘッダー・フッター・電話ポップアップへのメニュー追加(手順6)を行ってください
- 逆に、非公開の間はヘッダー・フッター・電話ポップアップへの追加(手順6)や、校舎一覧ページへの掲載は行わないでください(直接URLを知らない限り辿り着けない状態を保つため)


久我山校ページ(`/school/kugayama/`)の実装を確認した結果に基づく、センター南校ページの追加手順です。
このリポジトリはテーマの実体を持たない下書き置き場です。実際の反映はFTP・WordPress管理画面で行ってください。

## 前提の確認結果

- 校舎ページは **カテゴリーアーカイブページ**(`category.php`)として表示される
- `category.php` がカテゴリースラッグ(例: `kugayama`)を判定し、`templates/school_data/parts-〇〇.php` を読み込む
- 校舎ごとのブログ記事は、校舎カテゴリーの**子カテゴリー**(例: `blog-kg`)に投稿を割り当てて表示している
- 講師一覧は「Teacher」カスタム投稿タイプに校舎スラッグと同じタームを付けて自動抽出される
- ヘッダー・フッター・電話ポップアップの校舎一覧は手動でHTMLに追記されている(データベース連動ではない)

## 作業手順

### 1. カテゴリーを作成する(WordPress管理画面 → 投稿 → カテゴリー)

| 項目 | 値 |
|---|---|
| 名前 | センター南校 |
| スラッグ | `centerminami` |
| 親カテゴリー | 「校舎情報」(既存の`school`カテゴリー) |

続けて、その**子カテゴリー**として校舎ブログ用カテゴリーも作成します。

| 項目 | 値 |
|---|---|
| 名前 | センター南校ブログ |
| スラッグ | `blog-cm` |
| 親カテゴリー | センター南校(`centerminami`) |

作成後、「センター南校ブログ」カテゴリーの**カテゴリーID**を確認してください(カテゴリー一覧のリンクにマウスを乗せると `tag_ID=数字` がURLに表示されます)。このIDは手順5で使います。

### 2. `category.php` に分岐を追加する

`wp-content/themes/testea/category.php` を開き、`kugayama` の分岐ブロックの近くに以下を追記してください。

```php
if(is_category( 'centerminami' )): //センター南校
  get_template_part( 'templates/school_data/parts', 'centerminami' );
endif;
```

さらに、ブログ用カテゴリーをまとめて処理している以下の配列にも `blog-cm` を追加してください。

```php
// 変更前
if(is_category(array( 'blog-kg','blog-ne','blog-km','blog-hy','blog-jy', 'blog-ws', 'blog-mn','blog-ol', 'blog-sk', 'blog-ht','blog-ig' ))):
  get_template_part('renew/templates/category/category','blog');
endif;

// 変更後（blog-cm を追加）
if(is_category(array( 'blog-kg','blog-ne','blog-km','blog-hy','blog-jy', 'blog-ws', 'blog-mn','blog-ol', 'blog-sk', 'blog-ht','blog-ig','blog-cm' ))):
  get_template_part('renew/templates/category/category','blog');
endif;
```

### 3. 校舎ページ用CSS/JSの読み込み条件を確認する(★デザイン崩れの原因になりやすい箇所)

`parts-centerminami.php`のHTML構造自体は久我山校ページの出力と一致していても、**校舎ページ専用のCSS(`renew/school/css/style.css`など)がこの新しいカテゴリーで読み込まれていない**と、要素は表示されるのに横並びレイアウト・サムネイル整形・2カラム化などのスタイルだけが当たらない、という症状になります(教室長メッセージが写真とテキストで横並びにならない/ブログのサムネイルが原寸大で表示される/連絡先が1カラムの箇条書きになる、など)。

`functions.php`(または`wp_enqueue_scripts`フックが定義されている箇所)を開き、手順2の`category.php`の`blog-cm`配列と同様に、校舎スラッグをハードコードした配列があるか確認してください。例えば以下のような記述です。

```php
// 例(実際のコードはこの通りとは限りません)
if ( is_category( array( 'kugayama', 'nerima', 'komagome', 'hiyoshi', ... ) ) ) {
    wp_enqueue_style( 'school-style', get_stylesheet_directory_uri() . '/renew/school/css/style.css' );
}
```

このような配列が見つかった場合は、`'centerminami'`をその配列に追加してください。同様の配列がテーマ内の他の箇所(JSファイルの読み込み条件、`body_class`のフィルターなど)にもないか、念のため`kugayama`で検索して洗い出すことをおすすめします。

見当たらない場合(校舎ページ用CSSが常に全ページで読み込まれている場合)は、この手順は不要です。その場合はブラウザの開発者ツール(F12)で、実際のページに`renew/school/css/style.css`が読み込まれているか、ネットワークタブで確認してください。

### 4. `functions.php` のメタ情報上書き処理(任意)

自由が丘・駒込・日吉の3校舎には、メタディスクリプションとタイトルをカテゴリー単位で上書きする処理(`valleyin_meta_fix_start` など)が追加されています。これは必須ではなく、AIOSEOの「カテゴリー編集」画面から直接タイトル・ディスクリプションを設定すれば同様の効果が得られます。まずはAIOSEO側の設定で対応し、表示が崩れる場合のみ同様の分岐追加を検討してください。

### 5. テンプレートファイルをアップロードする

このリポジトリの `templates/school_data/parts-centerminami.php` を、
`wp-content/themes/testea/templates/school_data/parts-centerminami.php` としてアップロードしてください。

アップロード後、ファイル内の以下の箇所を編集してください。

```php
// TODO: 「センター南校ブログ」カテゴリー作成後、そのカテゴリーIDに変更してください
$blog_cat_id = 'XX';
```

ここに手順1で確認した「センター南校ブログ」カテゴリーのIDを入れてください。

### 6. ヘッダー・フッター・電話ポップアップに追加する

これらは久我山校ページのHTML出力から特定した箇所で、実ファイルの中身は未確認のため、**同じ構造の校舎(例: 日吉校)のブロックをコピーして書き換える**形で追加してください。

**ヘッダーの「校舎情報」プルダウン**(校舎一覧のリストに1件追加)

```html
<li><a href="https://testea.net/school/centerminami/">
    <figure>
      <span><img src="(校舎写真が決まるまでは既存の適当な画像で仮置き)" alt="school センター南"></span>
      <figcaption>センター南校</figcaption>
    </figure>
  </a></li>
```

**フッターのサイトマップ**(「校舎情報」の子リストに1件追加)

```html
<li><a href="https://testea.net/school/centerminami/">センター南校</a></li>
```

**画面右下の電話ポップアップ**

電話番号が未定のため、このリストへの追加は電話番号が決まってから行ってください。追加する際は以下の形式です。

```html
<li class="tel__item">
    <a href="tel:0X-XXXX-XXXX">
        <span class="school__name">センター南校</span>
        <span class="school__tel">0X-XXXX-XXXX</span></a>
</li>
```

## 今後、情報が決まり次第 更新が必要な箇所(`parts-centerminami.php` 内にもTODOコメントで記載済み)

1. `$blog_cat_id`(手順5)
2. 電話番号・受付時間・最寄駅の詳細アクセス
3. 教室長メッセージ・写真
4. 校舎の外観・内装スライダー画像
5. 道案内(アクセス写真)
6. 通塾エリア情報
7. Googleビジネスプロフィールのレビュー表示(`[grw id=...]`)

※住所(`〒224-0032 神奈川県横浜市都筑区茅ケ崎中央44-14 SHOKENセンター南ビル202`)はビル名変更予定とのことなので、確定後に `parts-centerminami.php` 内の住所とGoogleマップの表示も見直してください(現状はビル名を含めた住所でGoogle検索埋め込みにしているため、ビル名が変わっても検索自体は大きくは崩れませんが、確定後の再確認を推奨します)。
