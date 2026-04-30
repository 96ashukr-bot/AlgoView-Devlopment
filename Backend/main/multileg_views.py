from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.multileg_serializers import (
    MultiLegExecuteSerializer,
    MultiLegExitSerializer,
    MultiLegKillSwitchSerializer,
)
from main.services.multileg_execution import MultiLegExecutionError, get_multileg_execution_engine


class MultiLegExecuteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = MultiLegExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = get_multileg_execution_engine().execute(config=serializer.validated_data, user=request.user)
            return Response(payload, status=status.HTTP_201_CREATED)
        except MultiLegExecutionError as exc:
            return Response(
                {"detail": exc.message, "error_code": exc.error_code, "metadata": exc.metadata},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MultiLegActiveListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        client_id = request.query_params.get("client_id")
        payload = get_multileg_execution_engine().list_active(
            user=request.user,
            client_id=int(client_id) if client_id else None,
        )
        return Response(payload, status=status.HTTP_200_OK)


class MultiLegStrategyDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, execution_id, *args, **kwargs):
        try:
            payload = get_multileg_execution_engine().get_execution(execution_id, user=request.user, refresh_pnl=True)
            return Response(payload, status=status.HTTP_200_OK)
        except MultiLegExecutionError as exc:
            return Response(
                {"detail": exc.message, "error_code": exc.error_code, "metadata": exc.metadata},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MultiLegStrategyExitAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, execution_id, *args, **kwargs):
        serializer = MultiLegExitSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        try:
            payload = get_multileg_execution_engine().exit_execution(
                execution_id,
                user=request.user,
                reason=serializer.validated_data["reason"],
            )
            return Response(payload, status=status.HTTP_200_OK)
        except MultiLegExecutionError as exc:
            return Response(
                {"detail": exc.message, "error_code": exc.error_code, "metadata": exc.metadata},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MultiLegKillSwitchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = MultiLegKillSwitchSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        try:
            payload = get_multileg_execution_engine().kill_switch(
                user=request.user,
                client_id=serializer.validated_data.get("client_id"),
                reason=serializer.validated_data["reason"],
            )
            return Response(payload, status=status.HTTP_200_OK)
        except MultiLegExecutionError as exc:
            return Response(
                {"detail": exc.message, "error_code": exc.error_code, "metadata": exc.metadata},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MultiLegStrategyLogsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, execution_id, *args, **kwargs):
        try:
            payload = get_multileg_execution_engine().get_logs(execution_id, user=request.user)
            return Response(payload, status=status.HTTP_200_OK)
        except MultiLegExecutionError as exc:
            return Response(
                {"detail": exc.message, "error_code": exc.error_code, "metadata": exc.metadata},
                status=status.HTTP_400_BAD_REQUEST,
            )
