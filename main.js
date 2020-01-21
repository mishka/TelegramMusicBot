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
  
  if (match && match[2].length != 11) {
    print('URL not found in message!')
    return
  }

  const video_id = match[2]
  const { message, chat, from } = ctx
  const { first_name, username } = from
  const { message_id } = message
  const { id: chat_id } = chat

  print(`New request from: ${first_name}, ${username}, R${message_id}`)
  ctx.replyWithMarkdown('`Processing..`', Extra.inReplyTo(message_id))

  exec(`youtube-dl -e ${yt}${video_id}`, (error, stdout, stderr) => {
    if ((stdout.includes('ERROR')) || (!stdout.trim())) {
      ctx.telegram.editMessageText(chat_id, message_id + 1, void 0, `*Invalid ID.*`, Extra.markdown())
      print(`Invalid ID, skipping... R${message_id}`)
      return
    }

    const fileName = (stdout.replace(/\n|'|"|`/g, '')).replace(/[\/\\]/g,' ')
    const source = `${filesFolder}${fileName}.%(ext)s`

    print(`Found: ${fileName}`)

    let msg = `*Found:* \`${fileName}\`\n*Download started.*`

    ctx.telegram.editMessageText(chat_id, message_id + 1, void 0, msg, Extra.markdown())

    print(`Downloading... R${message_id}\n`)

    exec(`youtube-dl -x --audio-format mp3 -o "${source}" ${yt}${video_id}`, (_, stdout) => {
      print(`${stdout}\nDownload complete! Uploading... R${message_id}`)
      msg += `\n*Uploading…*`
      
      const source = `${filesFolder}${fileName}.mp3`
      ctx.telegram.editMessageText(chat_id, message_id + 1, void 0, msg, Extra.markdown())

      ctx.telegram.sendAudio(chat_id, { source }).then(() => {
        removeAsset(source, () => {
          print(`Completed! R${message_id}`)
          msg += `\n\n*Done!!*`
          ctx.telegram.editMessageText(chat_id, message_id + 1, void 0, msg, Extra.markdown())
        })
      }).catch(err => {
        print(err)
        var err_msg = '_Something went wrong while uploading the audio file, maybe try again later?_'
        ctx.telegram.editMessageText(chat_id, message_id + 1, void 0, err_msg, Extra.markdown())
      })
    })
  })
})

bot.launch()