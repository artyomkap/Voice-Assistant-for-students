import win32com.client
import tts


def get_first_5_emails():
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)  # 6 represents the Inbox folder

    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)  # Sort by received time to get the latest emails first
    new_messages = [msg for msg in messages if msg.UnRead]

    if new_messages:
        first_5_messages = []
        for i, message in enumerate(new_messages):
            if i >= 5:
                break
            first_5_messages.append(message)

        return first_5_messages
    else:
        return None


def check_new_emails_manual():
    global num_messages
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)  # 6 represents the Inbox folder

    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)  # Sort by ReceivedTime in descending order
    new_messages = [msg for msg in messages if msg.UnRead]

    if new_messages:
        return len(new_messages)
    else:
        return False


def check_new_emails_auto():
    global num_messages
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)  # 6 represents the Inbox folder

    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)  # Sort by ReceivedTime in descending order
    new_messages = [msg for msg in messages if msg.UnRead]
    if new_messages:
        return len(new_messages)
    else:
        return False
