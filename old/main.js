const fs = require('fs');
const exec = require('child_process').exec;
const moment = require('moment')
const Telegraf = require('telegraf')
const Extra = require('telegraf/extra')

const yt = 'https://youtube.com/watch?v='
const Token = ''
const exp = /^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*/

const bot = new Telegraf(Token)
const filesFolder = `${process.cwd()}/files/`

print('ONLINE.')

function print(it) {
  console.log(`[${moment().format('h:mm:ss')}] │ ${it}`)
}

function removeAsset(assetName, then) {
  return fs.unlink(assetName, err => {
    if (err) {
      console.error(err)
      return
    }

    if (typeof then === 'function') {
      then()
    }
  })
}

bot.on('text', ctx => {
  var temp = ctx.message.text
  var match = temp.match(exp)

  if (!match) {
    print('Match failed')
    return
  }

  const videoId = match[2]

  if (videoId.length != 11) {
    print('Invalid video ID!')
    return
  }

  const { message, chat, from } = ctx
  const { first_name: firstName, username } = from
  const { message_id: messageId } = message
  const { id: chatId } = chat

  print(`New request from: ${firstName}, ${username}, R${messageId}`)
  ctx.replyWithMarkdown('`Processing…`', Extra.inReplyTo(messageId))

  exec(`youtube-dl -e ${yt}${videoId}`, (_error, stdout, _stderr) => {
    if ((stdout.includes('ERROR')) || (!stdout.trim())) {
      ctx.telegram.editMessageText(chatId, messageId + 1, void 0, `*Invalid ID.*`, Extra.markdown())
      print(`Invalid ID, skipping... R${messageId}`)
      return
    }

    const fileName = (stdout.replace(/\n|'|"|`/g, '')).replace(/[\/\\]/g,' ')
    const source = `${filesFolder}${fileName}.%(ext)s`

    print(`Found: ${fileName}`)

    let msg = `*Found:* \`${fileName}\`\n*Download started.*`

    ctx.telegram.editMessageText(chatId, messageId + 1, void 0, msg, Extra.markdown())

    print(`Downloading... R${messageId}\n`)

    exec(`youtube-dl -x --audio-format mp3 -o "${source}" ${yt}${videoId}`, (_, stdout) => {
      print(`${stdout}\nDownload complete! Uploading... R${messageId}`)
      msg += '\n*Uploading…*'

      const source = `${filesFolder}${fileName}.mp3`
      ctx.telegram.editMessageText(chatId, messageId + 1, void 0, msg, Extra.markdown())

      ctx.telegram.sendAudio(chatId, { source }).then(() => {
        removeAsset(source, () => {
          print(`Completed! R${messageId}`)
          msg += '\n\n*Done!!*'
          ctx.telegram.editMessageText(chatId, messageId + 1, void 0, msg, Extra.markdown())
        })
      }).catch(err => {
        print(err)
        var err_msg = '_Something went wrong while uploading the audio file, maybe try again later?_'
        ctx.telegram.editMessageText(chatId, messageId + 1, void 0, err_msg, Extra.markdown())
      })
    })
  })
})

bot.launch()
