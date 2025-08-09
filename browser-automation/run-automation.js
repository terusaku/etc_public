#!/usr/bin/env node

import { execSync } from 'child_process';
import { existsSync } from 'fs';

// 引数チェック
const args = process.argv.slice(2);
if (args.length < 2) {
  console.log('使用方法: npm run auto <URL> "<操作内容>"');
  console.log('例: npm run auto "https://google.com" "検索ボックスに\'Hello\'と入力"');
  process.exit(1);
}

const [url, action] = args;

console.log('🚀 ブラウザ自動化を開始します...');
console.log(`📍 URL: ${url}`);
console.log(`🤖 操作: ${action}`);

try {
  // 必要な依存関係を確認・インストール
  console.log('\n🔧 環境を準備中...');
  
  // Playwright MCPサーバーのインストール確認
  try {
    execSync('which npx', { stdio: 'ignore' });
    console.log('✅ npx が利用可能です');
  } catch {
    console.error('❌ npx が見つかりません。Node.jsを正しくインストールしてください。');
    process.exit(1);
  }

  // Playwright ブラウザーのインストール（初回のみ）
  console.log('🌐 Playwrightブラウザーをチェック中...');
  try {
    execSync('npx playwright install', { stdio: 'inherit' });
    console.log('✅ Playwrightブラウザーの準備完了');
  } catch (error) {
    console.log('⚠️  Playwrightブラウザーのインストールをスキップ');
  }

  // MCP サーバーのグローバルインストール試行
  console.log('🎭 Playwright MCPサーバーをチェック中...');
  try {
    execSync('npm install -g @playwright/mcp@latest', { stdio: 'ignore' });
    console.log('✅ Playwright MCPサーバーの準備完了');
  } catch (error) {
    console.log('⚠️  グローバルインストールに失敗。ローカルで実行します。');
  }

  // メインアプリケーションを実行
  console.log('\n🎬 ブラウザ操作を開始...\n');
  execSync(`node index.js "${url}" "${action}"`, { 
    stdio: 'inherit',
    env: { ...process.env, FORCE_COLOR: 'true' }
  });

  console.log('\n🎉 操作が完了しました！');

} catch (error) {
  console.error('\n❌ エラーが発生しました:', error.message);
  process.exit(1);
}
