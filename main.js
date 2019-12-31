const fs = require('fs');
const exec = require('child_process').exec;
const moment = require('moment')
const Telegraf = require('telegraf')
const Extra = require('telegraf/extra')
const Token = ''
const yt = 'https://youtube.com/watch?v='

const bot = new Telegraf(Token)
const filesFolder = `${process.cwd()}/files/`

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

print(`Waiting for requests.`)

bot.on('text', ctx => {
  var temp = ctx.message.text

  if ((temp.length != 11) || (/[a-zA-Z0-9_-]{11}/g.exec(temp) == null)) {
    print(`Invalid input, skipping..`)
    return
  } else if (/;|&|#|\|/g.exec(temp)) {
    print(`FORBIDDEN CHARACTERS, SKIPPING! (angery)`)
    ctx.replyWithMarkdown(`*you shan't pass*`, Extra.inReplyTo(ctx.message.message_id))
    return
  }

  const { message, chat, from } = ctx
  const { first_name, username } = from
  const { message_id } = message
  const { id: chat_id } = chat
  const { text: url } = ctx.message

  print(`New request from: ${first_name}, ${username}, R${message_id}`)
  ctx.replyWithMarkdown('`Processing..`', Extra.inReplyTo(message_id))

  exec(`youtube-dl -e ${yt}${url}`, (error, stdout, stderr) => {
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

    exec(`youtube-dl -x --audio-format mp3 -o "${source}" ${yt}${url}`, (_, stdout) => {
      print(`${stdout}\nDownload complete! Uploading... R${message_id}`)
      msg += `\n*Uploading…*`

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