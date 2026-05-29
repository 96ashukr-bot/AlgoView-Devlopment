from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import ChatMessage, ChatThread, User
from main.permissions import can_access_client_record, get_accessible_clients_queryset, is_end_user, is_platform_admin, is_subadmin_user
from main.serializers import ChatMessageSerializer, ChatThreadSerializer


def _sender_role(user):
    if is_platform_admin(user):
        return ChatMessage.SENDER_SUPERADMIN
    if is_subadmin_user(user):
        return ChatMessage.SENDER_SUBADMIN
    return ChatMessage.SENDER_CLIENT


def _message_read_flags(sender_role):
    return {
        "is_read_by_client": sender_role == ChatMessage.SENDER_CLIENT,
        "is_read_by_staff": sender_role in {ChatMessage.SENDER_SUBADMIN, ChatMessage.SENDER_SUPERADMIN},
    }


def _thread_queryset_for_user(user):
    queryset = ChatThread.objects.select_related("client", "assigned_subadmin")
    if is_platform_admin(user):
        return queryset
    if is_subadmin_user(user):
        return queryset.filter(client__assigned_client=user)
    return queryset.filter(client=user)


def _annotate_thread_queryset(queryset, user):
    if is_end_user(user):
        unread_filter = Q(messages__sender_role__in=[ChatMessage.SENDER_SUBADMIN, ChatMessage.SENDER_SUPERADMIN], messages__is_read_by_client=False)
    else:
        unread_filter = Q(messages__sender_role=ChatMessage.SENDER_CLIENT, messages__is_read_by_staff=False)
    return queryset.annotate(
        unread_count=Count("messages", filter=unread_filter),
        messages_count=Count("messages"),
    )


def _get_accessible_thread(user, thread_id):
    return _thread_queryset_for_user(user).filter(id=thread_id).first()


def _mark_thread_read_for_user(thread, user):
    if is_end_user(user):
        thread.messages.filter(
            sender_role__in=[ChatMessage.SENDER_SUBADMIN, ChatMessage.SENDER_SUPERADMIN],
            is_read_by_client=False,
        ).update(is_read_by_client=True)
    else:
        thread.messages.filter(sender_role=ChatMessage.SENDER_CLIENT, is_read_by_staff=False).update(is_read_by_staff=True)


def _unread_message_queryset_for_user(user):
    queryset = ChatMessage.objects.filter(thread__in=_thread_queryset_for_user(user))
    if is_end_user(user):
        return queryset.filter(
            sender_role__in=[ChatMessage.SENDER_SUBADMIN, ChatMessage.SENDER_SUPERADMIN],
            is_read_by_client=False,
        )
    return queryset.filter(sender_role=ChatMessage.SENDER_CLIENT, is_read_by_staff=False)


class ChatUnreadCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unread_messages = _unread_message_queryset_for_user(request.user)
        return Response(
            {
                "unread_count": unread_messages.count(),
                "unread_thread_count": unread_messages.values("thread_id").distinct().count(),
            }
        )


class ChatThreadListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = _thread_queryset_for_user(request.user)
        status_filter = str(request.query_params.get("status") or "").strip().lower()
        search = str(request.query_params.get("search") or "").strip()
        client_id = request.query_params.get("client_id")

        if status_filter in {ChatThread.STATUS_OPEN, ChatThread.STATUS_RESOLVED}:
            queryset = queryset.filter(status=status_filter)
        if client_id and str(client_id).isdigit():
            queryset = queryset.filter(client_id=int(client_id))
        if search:
            queryset = queryset.filter(
                Q(subject__icontains=search)
                | Q(client__firstName__icontains=search)
                | Q(client__lastName__icontains=search)
                | Q(client__fullName__icontains=search)
                | Q(client__email__icontains=search)
                | Q(messages__message__icontains=search)
            ).distinct()

        queryset = _annotate_thread_queryset(queryset, request.user).order_by("-last_message_at", "-id")[:100]
        return Response({"results": ChatThreadSerializer(queryset, many=True).data})

    def post(self, request):
        message = str(request.data.get("message") or "").strip()
        subject = str(request.data.get("subject") or "").strip()
        if not message:
            return Response({"message": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)

        if is_end_user(request.user):
            client = request.user
        else:
            client_id = request.data.get("client_id")
            if not client_id:
                return Response({"message": "Client is required."}, status=status.HTTP_400_BAD_REQUEST)
            client = User.objects.filter(id=client_id).first()
            if not client or not can_access_client_record(request.user, client):
                return Response({"message": "You cannot create chat for this client."}, status=status.HTTP_403_FORBIDDEN)

        thread = ChatThread.objects.create(
            client=client,
            assigned_subadmin=client.assigned_client,
            subject=subject[:255],
            last_message_at=timezone.now(),
        )
        sender_role = _sender_role(request.user)
        ChatMessage.objects.create(
            thread=thread,
            sender=request.user,
            sender_role=sender_role,
            message=message,
            **_message_read_flags(sender_role),
        )
        serializer = ChatThreadSerializer(_annotate_thread_queryset(ChatThread.objects.filter(id=thread.id), request.user).first())
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatThreadDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        thread = _get_accessible_thread(request.user, thread_id)
        if not thread:
            return Response({"message": "Chat thread not found."}, status=status.HTTP_404_NOT_FOUND)
        _mark_thread_read_for_user(thread, request.user)
        thread = _annotate_thread_queryset(ChatThread.objects.select_related("client", "assigned_subadmin").filter(id=thread.id), request.user).first()
        messages = ChatMessage.objects.select_related("sender").filter(thread=thread).order_by("created_at", "id")[:500]
        return Response(
            {
                "thread": ChatThreadSerializer(thread).data,
                "messages": ChatMessageSerializer(messages, many=True).data,
            }
        )

    def patch(self, request, thread_id):
        thread = _get_accessible_thread(request.user, thread_id)
        if not thread:
            return Response({"message": "Chat thread not found."}, status=status.HTTP_404_NOT_FOUND)
        if is_end_user(request.user):
            return Response({"message": "Only staff can update chat status."}, status=status.HTTP_403_FORBIDDEN)

        next_status = str(request.data.get("status") or "").strip().lower()
        if next_status not in {ChatThread.STATUS_OPEN, ChatThread.STATUS_RESOLVED}:
            return Response({"message": "Invalid chat status."}, status=status.HTTP_400_BAD_REQUEST)
        thread.status = next_status
        thread.save(update_fields=["status", "updated_at"])
        thread = _annotate_thread_queryset(ChatThread.objects.select_related("client", "assigned_subadmin").filter(id=thread.id), request.user).first()
        return Response(ChatThreadSerializer(thread).data)


class ChatMessageCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        thread = _get_accessible_thread(request.user, thread_id)
        if not thread:
            return Response({"message": "Chat thread not found."}, status=status.HTTP_404_NOT_FOUND)

        message = str(request.data.get("message") or "").strip()
        if not message:
            return Response({"message": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)

        sender_role = _sender_role(request.user)
        chat_message = ChatMessage.objects.create(
            thread=thread,
            sender=request.user,
            sender_role=sender_role,
            message=message,
            **_message_read_flags(sender_role),
        )
        thread.status = ChatThread.STATUS_OPEN
        thread.assigned_subadmin = thread.client.assigned_client
        thread.last_message_at = chat_message.created_at
        thread.save(update_fields=["status", "assigned_subadmin", "last_message_at", "updated_at"])
        return Response(ChatMessageSerializer(chat_message).data, status=status.HTTP_201_CREATED)


class ChatAccessibleClientListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if is_end_user(request.user):
            return Response({"results": []})
        clients = get_accessible_clients_queryset(request.user).order_by("fullName", "email")[:500]
        return Response(
            {
                "results": [
                    {
                        "id": client.id,
                        "name": client.fullName or client.get_full_name() or client.email,
                        "email": client.email,
                    }
                    for client in clients
                ]
            }
        )
