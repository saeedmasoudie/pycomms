import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils.timezone import now

from home.models import ChannelMember, ChannelMessage
from user.models import CustomUser
from utils.checkers import get_country_code


class WebRTCConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.user = self.scope['user']
        if not self.user:
            await self.close()
            return
        self.username = self.user.username
        self.user_id = str(self.user.id)
        self.full_name = self.user.full_name()
        self.avatar_url = self.user.avatar.url if self.user.avatar else '/static/images/avatar.jpg'
        client_ip = self.scope.get('client')[0]
        self.room_group_name = f"channel_{self.channel_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        asyncio.create_task(mark_user_active(self.username, self.channel_id))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_update",
                "action": "join",
                "username": self.username,
                "name": self.full_name,
                "userId": self.user_id,
                "channelId": self.channel_id,
                "flag": get_country_code(client_ip),
                "avatar": self.avatar_url,
            }
        )

    async def disconnect(self, close_code):
        if self.username:
            asyncio.create_task(mark_user_inactive(self.username, self.channel_id))
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_update",
                    "action": "leave",
                    "username": self.username,
                    "userId": self.user_id,
                    "channelId": self.channel_id,
                }
            )

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")
        data['fromUserId'] = self.user_id
        data['fromUsername'] = self.username

        if message_type == "ready_to_connect":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_message",
                    "message": data
                }
            )

        elif message_type in ["webrtc_offer", "webrtc_answer", "webrtc_ice_candidate"]:
            target_user_id = data.get("targetUserId")
            if target_user_id:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "send_to_specific_user",
                        "message": data,
                        "target_user_id": target_user_id
                    }
                )
            else:
                print(f"Warning: {message_type} received without targetUserId")

        elif message_type == "user_update":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_update",
                    "action": data["action"],
                    "username": data["username"],
                    "userId": self.user_id,
                }
            )

        elif message_type == "chat_message":
            message = data.get('message', '').strip()
            username = data.get('username', '').strip()

            if message and username:  # Ensure valid data
                timestamp = now().strftime("%H:%M:%S")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        'username': username,
                        'message': message,
                        'timestamp': timestamp,
                        'avatar': self.avatar_url
                    }
                )
                asyncio.create_task(save_channel_message(self.channel_id, username, message))

        elif message_type == "ping":
            sender = data.get("sender", "Unknown")
            await self.send(text_data=json.dumps({"type": "pong", "sender": sender}))

        elif message_type == "voice_status":
            is_talking = data["is_talking"]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "voice_activity",
                    "username": self.username,
                    "is_talking": is_talking
                }
            )
        elif message_type == "update_ping":
            sender = data.get("sender", "Unknown")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_ping",
                    "sender": sender,
                    "ping": data["ping"],
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def broadcast_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps(message))

    async def send_to_specific_user(self, event):
        message = event["message"]
        target_user_id = event["target_user_id"]
        if str(self.user.id) == target_user_id:
            await self.send(text_data=json.dumps(message))

    async def broadcast_ping(self, event):
        await self.send(text_data=json.dumps({
            "type": "update_ping",
            "sender": event["sender"],
            "ping": event["ping"]
        }))

    async def user_update(self, event):
        if event["username"] != self.username:
            await self.send(text_data=json.dumps(event))

    async def voice_activity(self, event):
        username = event["username"]
        is_talking = event["is_talking"]

        await self.send(text_data=json.dumps({
            "type": "voice_activity",
            "username": username,
            "is_talking": is_talking
        }))

@sync_to_async
def mark_user_active(username, channel_id):
    user = CustomUser.objects.filter(username=username).only("id").first()
    if user:
        ChannelMember.objects.update_or_create(user=user, channel_id=channel_id, defaults={'active': True})

@sync_to_async
def mark_user_inactive(username, channel_id):
    user = CustomUser.objects.filter(username=username).only("id").first()
    if user:
        ChannelMember.objects.filter(user=user, channel_id=channel_id).update(active=False)

@sync_to_async
def save_channel_message(channel_id, username, content):
    user = CustomUser.objects.filter(username=username).only("id").first()
    if user:
        ChannelMessage.objects.create(
            channel_id=channel_id,
            sender=user,
            content=content,
            timestamp=now()
        )