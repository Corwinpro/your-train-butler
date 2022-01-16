# Your Train Butler

This repo contains code for a Telegram bot that serves as a personal butler for train travels in the UK.

This bot can:

- Show live departures from a station or between stations,
- Notify about service disruptions on your regular travels.

*Note*: this is still a very much work in progress project. Please feel free to open bug reports, feature requests, or a general suggestion.

## Give it a try!

Find the [`@train_check_bot`](https://t.me/train_check_bot) in Telegram, and type `/help` to see what the bot can do for you. This will show a list of available commands.

### Live departures

To see live departures from London Kings Cross station, send

```
/board KGX
```

To see live departures between London Kings Cross and Cambridge, send the destination as the second argument:

```
/board KGX CBG
```

### Service notifications

If you regularly commute between stations and want the bot to notify you about possible delays or cancellation, subscribe to a journey:

```
 /subscribe KGX CBG 12:23
```

The bot will keep an eye on the official Rail Network notifications, and send you a message in case anything goes wrong.

You can see and cancel your subscriptions using the  `/unsubscribe` command.
It is also possible to unsubscribe from a service manually with `/unsubscribe KGX CBG 12:23` (specify the origin, the destination, and the time).
To unsubscribe from all notifications, type `/unsubscribe all`.