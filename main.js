const fs = require('fs');
const exec = require('child_process').exec;
const moment = require('moment')
const Telegraf = require('telegraf')
const Extra = require('telegraf/extra')
const pattern = /^(http(s)?:\/\/)?((w){3}.)?youtu(be|.be)?(\.com)?\/.+/gm;
const Token = ''

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

bot.on('text', ctx => {
  const result = pattern.exec(ctx.message.text)

  if (!result) {
    // TODO: Show an error message here
    return
  }

  const { message, chat, from } = ctx
  const { first_name, username } = from
  const { message_id } = message
  const { id: chat_id } = chat
  const [ url ] = result

  print(`New request from: ${first_name}, ${username}`)
  ctx.replyWithMarkdown('`Processing..`', Extra.inReplyTo(message_id))

  exec(`youtube-dl -e ${url}`, (_, stdout) => {
    const fileName = (stdout.replace(/\n|'|"|`/g, '')).replace(/[\/\\]/g,' ')
    const source = `${filesFolder}${fileName}.mp3`

    print(`Found: ${fileName}`)

    let msg = `*Found:* \`${fileName}\`\n*Download started.*`

    ctx.telegram.editMessageText(chat_id, message_id + 1, void 0, msg, Extra.markdown())

    print('Downloading…\n')

    exec(`youtube-dl -x --audio-format mp3 -o "${source}" ${url}`, (_, stdout) => {
      print(stdout)
      print('Download complete! Uploading…')
      msg += `\n*Uploading…*`

      ctx.telegram.editMessageText(chat_id, message_id + 1, void 0, msg, Extra.markdown())

      ctx.telegram.sendAudio(chat_id, { source }).then(() => {
        removeAsset(source, () => {
          print('Done')
          msg += `\n\n*Done!!*`
          ctx.telegram.editMessageText(chat_id, message_id + 1, void 0, msg, Extra.markdown())
        })
      })
    })
  })
})

bot.launch()
