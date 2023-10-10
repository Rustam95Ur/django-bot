from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.base import BaseIdModel


class UserChatSetting(BaseIdModel):
    """UserChatSetting"""
    user = models.OneToOneField(
        User,
        related_name="chat_settings",
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    bot_token = models.CharField(
        verbose_name=_("Bot token"),
        max_length=20
    )

    class Meta:
        verbose_name = _("User Chat Setting")
        verbose_name_plural = _("User Chat Settings")
        db_table = "user_chat_settings"


class UseChatHistory(BaseIdModel):
    """UseChatHistory"""

    user = models.ForeignKey(
        User,
        related_name="chats",
        verbose_name=_("User"),
        on_delete=models.CASCADE
    )
    message = models.TextField(
        verbose_name=_("Message")
    )

    class Meta:
        verbose_name = _("User Chat History")
        verbose_name_plural = _("User Chat Histories")
        db_table = "user_chat_histories"
