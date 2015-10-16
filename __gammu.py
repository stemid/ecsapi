import gammu

class GammuPlugin(ecs.BasePlugin):
    def send_message(recipient, message):
        sm = gammu.StateMachine()

        if config.has_option('api', 'gammu_config'):
            sm.ReadConfig(Filename=config.get('api', 'gammu_config'))
        else:
            # Read ~/.gammurc
            sm.ReadConfig()

        sm.Init()

        if len(message) < 160:
            sms = {
                'Text': message,
                'SMSC': {'Location': 1},
                'Number': recipient
            }

            sm.SendSMS(sms)
        else:
            sms = {
                'Class': 1,
                'Unicode': True,
                'Entries': [
                    {
                        'ID': 'ConcatenatedTextLong',
                        'Buffer': message
                    }
                ]
            }

            encoded = gammu.EncodeSMS(sms)

            for _part in encoded:
                _part['SMSC'] = {'Location': 1}
                _part['Number'] = recipient

                sm.SendSMS(_part)


