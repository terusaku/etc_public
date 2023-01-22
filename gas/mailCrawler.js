// Gmailの検索機能を使って該当するメールを見つけたらSlack Webhookで通知する

function myFunction() {
    const threads = GmailApp.search('from:{senderName}}');
    threads.forEach(function(thread) {
      const msgs = thread.getMessages();
      msgs.forEach(function(msg) {
        let recvDate = msg.getDate();
        let sub = msg.getSubject();
        let body = msg.getPlainBody();
        let payment = body.match(/{Regex:searchKeyWord}}/);
        let postMsg = `
        受信日時: ${recvDate}
        件名: ${sub}
        本文: ${body}
        金額: ${payment}
        `
        postSlack(postMsg);
      })
  
    });
  }
  
  async function postSlack(postMsg) {
      const slackChannel = {ChannelId};
      const slackToken = {botToken};
      const slackUrl = 'https://slack.com/api/chat.postMessage';
      const payload = {
        channel: slackChannel,
        token: slackToken,
        text: postMsg,
      };
      const opts = {
        'method': 'post',
        'payload': payload
      };
       let resData = UrlFetchApp.fetch(slackUrl, opts).getContentText();
       console.log(resData);  
  }