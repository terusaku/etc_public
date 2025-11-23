#!/usr/bin/env node

import { chromium, Browser, Page } from 'playwright';
import * as fs from 'fs';
import * as readline from 'readline';

interface UserInfo {
  zennId: string;
  displayName: string;
  github?: string;
  twitter?: string;
  profileUrl: string;
}

interface ScraperConfig {
  articleSlug: string;  // 記事のスラッグ（URLの最後の部分）
  outputPath: string;
  delayMs: number;
}

class ZennLikesScraper {
  private browser: Browser | null = null;
  private page: Page | null = null;
  private config: ScraperConfig;

  constructor(config: ScraperConfig) {
    this.config = config;
  }

  async initialize(): Promise<void> {
    console.log('🚀 ブラウザを起動中...');
    this.browser = await chromium.launch({
      headless: false,  // 手動ログイン用に表示
    });
    this.page = await this.browser.newPage();

    await this.page.setExtraHTTPHeaders({
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    });
  }

  private async waitForUserInput(message: string): Promise<void> {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    return new Promise((resolve) => {
      rl.question(message, () => {
        rl.close();
        resolve();
      });
    });
  }

  async login(): Promise<void> {
    if (!this.page) throw new Error('Page not initialized');

    console.log('📄 Zennログインページにアクセス中...');
    await this.page.goto('https://zenn.dev/enter', { waitUntil: 'networkidle' });

    console.log('\n' + '='.repeat(50));
    console.log('🔐 ブラウザでZennにログインしてください');
    console.log('   (Google/GitHub/Twitter認証が使えます)');
    console.log('='.repeat(50) + '\n');

    await this.waitForUserInput('ログイン完了後、Enterキーを押してください...');

    // ログイン確認
    await this.page.goto('https://zenn.dev/dashboard', { waitUntil: 'networkidle' });
    const isLoggedIn = await this.page.$('[class*="Header"] [class*="avatar"], [class*="UserMenu"]');

    if (!isLoggedIn) {
      console.log('⚠️ ログインが確認できません。続行しますか？');
      await this.waitForUserInput('Enterキーで続行...');
    } else {
      console.log('✅ ログイン確認完了');
    }
  }

  async getLikersFromNotifications(): Promise<string[]> {
    if (!this.page) throw new Error('Page not initialized');

    console.log('🔔 通知ページにアクセス中...');
    await this.page.goto('https://zenn.dev/notifications', { waitUntil: 'networkidle' });
    await this.delay(2000);

    const users: string[] = [];
    const articleSlug = this.config.articleSlug;

    console.log(`📝 対象記事: ${articleSlug}`);
    console.log('いいね通知を検索中...');

    // ページをスクロールしてすべての通知を読み込む
    let previousHeight = 0;
    let scrollAttempts = 0;
    const maxScrollAttempts = 20;

    while (scrollAttempts < maxScrollAttempts) {
      // 現在表示されている通知からいいねユーザーを抽出
      const newUsers = await this.page.$$eval(
        'a[href^="/"]',
        (links, slug) => {
          const results: string[] = [];

          // 通知アイテムを探す
          const notificationItems = document.querySelectorAll('[class*="notification"], [class*="Notification"], li, article');

          notificationItems.forEach(item => {
            const text = item.textContent || '';
            // いいね通知で、対象記事に関するもの
            if ((text.includes('いいね') || text.includes('liked')) && text.includes(slug)) {
              // ユーザーリンクを抽出
              const userLinks = item.querySelectorAll('a[href^="/"]');
              userLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href && href.match(/^\/[a-zA-Z0-9_-]+$/) && !href.includes('/articles')) {
                  results.push(href.replace('/', ''));
                }
              });
            }
          });

          return results;
        },
        articleSlug
      );

      // 新しいユーザーを追加
      newUsers.forEach(user => {
        if (!users.includes(user)) {
          users.push(user);
        }
      });

      // スクロール
      const currentHeight = await this.page.evaluate(() => document.body.scrollHeight);
      if (currentHeight === previousHeight) {
        scrollAttempts++;
      } else {
        scrollAttempts = 0;
        previousHeight = currentHeight;
      }

      await this.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await this.delay(1000);
    }

    // 代替方法: 全リンクからユーザーを抽出
    if (users.length === 0) {
      console.log('⚠️ 通知からの抽出に失敗。ページ全体から検索します...');

      const allUsers = await this.page.$$eval(
        'a[href^="/"]',
        (links) => links
          .map(link => {
            const href = link.getAttribute('href');
            if (href && href.match(/^\/[a-zA-Z0-9_-]+$/)) {
              return href.replace('/', '');
            }
            return null;
          })
          .filter((id): id is string => id !== null)
      );

      // 重複除去と既知のパスを除外
      const excludeList = ['dashboard', 'notifications', 'settings', 'articles', 'books', 'scraps', 'search', 'explore', 'faq', 'about', 'terms', 'privacy', 'guide'];
      allUsers.forEach(user => {
        if (!users.includes(user) && !excludeList.includes(user)) {
          users.push(user);
        }
      });
    }

    console.log(`✅ ${users.length} 人のユーザーを検出`);
    return users;
  }

  async getUserProfile(zennId: string): Promise<UserInfo> {
    if (!this.page) throw new Error('Page not initialized');

    const profileUrl = `https://zenn.dev/${zennId}`;
    console.log(`👤 プロフィール取得中: ${zennId}`);

    await this.page.goto(profileUrl, { waitUntil: 'networkidle' });
    await this.delay(this.config.delayMs);

    // 表示名を取得
    let displayName = zennId;
    try {
      const nameElement = await this.page.$('h1, [class*="name"], [class*="displayName"]');
      if (nameElement) {
        displayName = await nameElement.textContent() || zennId;
      }
    } catch {
      // デフォルトの zennId を使用
    }

    // SNSリンクを取得
    let github: string | undefined;
    let twitter: string | undefined;

    // GitHub リンク
    const githubLink = await this.page.$('a[href*="github.com"]');
    if (githubLink) {
      const href = await githubLink.getAttribute('href');
      if (href) {
        const match = href.match(/github\.com\/([^\/\?]+)/);
        github = match ? match[1] : undefined;
      }
    }

    // Twitter/X リンク
    const twitterLink = await this.page.$('a[href*="twitter.com"], a[href*="x.com"]');
    if (twitterLink) {
      const href = await twitterLink.getAttribute('href');
      if (href) {
        const match = href.match(/(?:twitter|x)\.com\/([^\/\?]+)/);
        twitter = match ? match[1] : undefined;
      }
    }

    return {
      zennId,
      displayName: displayName.trim(),
      github,
      twitter,
      profileUrl
    };
  }

  async scrape(): Promise<UserInfo[]> {
    const users: UserInfo[] = [];

    try {
      await this.initialize();
      await this.login();

      // 通知からいいねユーザーを取得
      const likerIds = await this.getLikersFromNotifications();

      if (likerIds.length === 0) {
        console.log('⚠️ いいねしたユーザーが見つかりませんでした');
        return users;
      }

      console.log(`\n📊 ${likerIds.length} 人のプロフィールを取得します...\n`);

      // 各ユーザーのプロフィールを取得
      for (let i = 0; i < likerIds.length; i++) {
        const zennId = likerIds[i];
        console.log(`[${i + 1}/${likerIds.length}] `);

        try {
          const userInfo = await this.getUserProfile(zennId);
          users.push(userInfo);

          const snsInfo = [];
          if (userInfo.github) snsInfo.push(`GitHub: ${userInfo.github}`);
          if (userInfo.twitter) snsInfo.push(`Twitter: ${userInfo.twitter}`);
          console.log(`  → ${userInfo.displayName} ${snsInfo.length > 0 ? `(${snsInfo.join(', ')})` : '(SNS未設定)'}`);
        } catch (error) {
          console.error(`  → ❌ 取得失敗: ${error}`);
          users.push({
            zennId,
            displayName: zennId,
            profileUrl: `https://zenn.dev/${zennId}`
          });
        }
      }

      return users;
    } finally {
      await this.close();
    }
  }

  async saveResults(users: UserInfo[]): Promise<void> {
    // JSON形式で保存
    const jsonPath = this.config.outputPath.replace(/\.[^.]+$/, '.json');
    fs.writeFileSync(jsonPath, JSON.stringify(users, null, 2), 'utf-8');
    console.log(`\n📁 JSON保存: ${jsonPath}`);

    // CSV形式で保存
    const csvPath = this.config.outputPath.replace(/\.[^.]+$/, '.csv');
    const csvHeader = 'zennId,displayName,github,twitter,profileUrl\n';
    const csvRows = users.map(u =>
      `"${u.zennId}","${u.displayName}","${u.github || ''}","${u.twitter || ''}","${u.profileUrl}"`
    ).join('\n');
    fs.writeFileSync(csvPath, csvHeader + csvRows, 'utf-8');
    console.log(`📁 CSV保存: ${csvPath}`);
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async close(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
      console.log('\n🔄 ブラウザを終了しました');
    }
  }
}

// メイン実行
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
使用方法: npm run scrape-zenn <記事スラッグ> [出力ファイル] [遅延ms]

例:
  npm run scrape-zenn 20251109_datadog_statistics_mapping
  npm run scrape-zenn 20251109_datadog_statistics_mapping ./output.json 2000

注意:
  - 記事作成者本人としてZennにログインする必要があります
  - 通知ページからいいねしたユーザーを取得します
`);
    process.exit(1);
  }

  const articleSlug = args[0];
  const outputPath = args[1] || './zenn-likers-result.json';
  const delayMs = parseInt(args[2] || '1500', 10);

  console.log('='.repeat(50));
  console.log('Zenn いいねユーザー情報スクレイパー');
  console.log('='.repeat(50));
  console.log(`記事スラッグ: ${articleSlug}`);
  console.log(`出力先: ${outputPath}`);
  console.log(`遅延: ${delayMs}ms`);
  console.log('='.repeat(50));

  const scraper = new ZennLikesScraper({
    articleSlug,
    outputPath,
    delayMs
  });

  try {
    const users = await scraper.scrape();

    if (users.length > 0) {
      await scraper.saveResults(users);

      console.log('\n📊 サマリー');
      console.log('='.repeat(50));
      console.log(`総ユーザー数: ${users.length}`);
      console.log(`GitHub設定あり: ${users.filter(u => u.github).length}`);
      console.log(`Twitter設定あり: ${users.filter(u => u.twitter).length}`);
      console.log(`両方設定あり: ${users.filter(u => u.github && u.twitter).length}`);
    }
  } catch (error) {
    console.error('❌ スクレイピング中にエラーが発生:', error);
    process.exit(1);
  }
}

main();
