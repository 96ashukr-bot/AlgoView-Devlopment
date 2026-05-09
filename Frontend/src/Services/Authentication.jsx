import axios, { requestTokenRefresh } from "./apiClient";
import {
  baseUrl,
  REMOTE_API_BASE_URL,
  clearPreferredBackend,
  getLocalApiBaseUrl,
  getLocalWsBaseUrl,
  getWsBaseUrlForApi,
  setPreferredBackend,
} from "../ConfigUrl/config";
import { getAuthToken } from "../ConfigUrl/config";
import Swal from 'sweetalert2';
import { showAlert, handleAuthError, handleNoTokenError } from "../ConfigUrl/config";
import { toast } from "react-toastify";
import {
  clearAuthTokens,
  getAccessToken,
  getAuthenticatedApiBaseUrl,
  getBrokerApiBaseUrl,
  getRefreshToken,
  setBrokerBackend,
  setAuthenticatedBackend,
  setAuthTokens,
} from "./authStorage";

const authDebug = (event, details = {}) => {
  if (typeof window === "undefined" || process.env.NODE_ENV === "production") {
    return;
  }
  console.info("[auth-debug]", event, details);
};

const persistAuthenticatedBackend = (candidateBaseUrl) => {
  const normalizedCandidateBaseUrl = candidateBaseUrl.replace(/\/$/, "");
  const normalizedLocalApiBaseUrl = getLocalApiBaseUrl().replace(/\/$/, "");
  const isLocalCandidate = normalizedCandidateBaseUrl === normalizedLocalApiBaseUrl;
  const nextWsBaseUrl = isLocalCandidate
    ? getLocalWsBaseUrl()
    : getWsBaseUrlForApi(normalizedCandidateBaseUrl);

  setPreferredBackend({
    apiBaseUrl: normalizedCandidateBaseUrl,
    wsBaseUrl: nextWsBaseUrl,
    force: !isLocalCandidate,
  });
  setAuthenticatedBackend({
    apiBaseUrl: normalizedCandidateBaseUrl,
    wsBaseUrl: nextWsBaseUrl,
  });
  authDebug("backend:persist", {
    backend: normalizedCandidateBaseUrl,
    isLocalCandidate,
  });
};

const persistBrokerBackend = (candidateBaseUrl) => {
  const normalizedCandidateBaseUrl = candidateBaseUrl.replace(/\/$/, "");
  const normalizedLocalApiBaseUrl = getLocalApiBaseUrl().replace(/\/$/, "");
  const isLocalCandidate = normalizedCandidateBaseUrl === normalizedLocalApiBaseUrl;
  const nextWsBaseUrl = isLocalCandidate
    ? getLocalWsBaseUrl()
    : getWsBaseUrlForApi(normalizedCandidateBaseUrl);

  setBrokerBackend({
    apiBaseUrl: normalizedCandidateBaseUrl,
    wsBaseUrl: nextWsBaseUrl,
  });
  authDebug("broker-backend:persist", {
    backend: normalizedCandidateBaseUrl,
    isLocalCandidate,
  });
};

export const login = async (email, password) => {
  clearAuthTokens();
  clearPreferredBackend();
  if (typeof window !== "undefined") {
    window.localStorage.removeItem("pendingOtpEmail");
    window.localStorage.removeItem("pendingOtpApiBaseUrl");
  }

  const attemptLogin = async (targetBaseUrl) => {
    return axios.post(`${targetBaseUrl}/login/`, {
      email,
      password,
    }, {
      skipAuthRefresh: true,
    });
  };

  const localApiBaseUrl = getLocalApiBaseUrl();
  const primaryBaseUrl = baseUrl || localApiBaseUrl;
  const alternateBaseUrl =
    baseUrl.replace(/\/$/, "") === localApiBaseUrl.replace(/\/$/, "") ? REMOTE_API_BASE_URL : localApiBaseUrl;

  try {
    let response;
    let authenticatedBaseUrl = primaryBaseUrl;

    try {
      authDebug("login:attempt", { backend: primaryBaseUrl });
      response = await attemptLogin(primaryBaseUrl);
    } catch (primaryError) {
      const canFallback =
        alternateBaseUrl.replace(/\/$/, "") !== primaryBaseUrl.replace(/\/$/, "") &&
        (
          primaryError.message?.includes("Network Error") ||
          primaryError.response?.status === 400 ||
          primaryError.response?.status === 401
        );

      if (!canFallback) {
        throw primaryError;
      }

      authDebug("login:fallback-attempt", {
        primaryBackend: primaryBaseUrl,
        alternateBackend: alternateBaseUrl,
        status: primaryError?.response?.status || null,
      });
      response = await attemptLogin(alternateBaseUrl);
      authenticatedBaseUrl = alternateBaseUrl;
      persistAuthenticatedBackend(authenticatedBaseUrl);
    }

    // Check for "success": ["False"] and handle it with Swal
    if (response.data.success?.includes("False")) {
      Swal.fire({
        icon: 'warning',
        title: 'License Expired',
        text: 'Your license has been expired. Please renew it to continue using the service. Please contact the administrator, and for more information, check your "Email".',
        confirmButtonText: 'OK',
      });
      return; // Stop execution to prevent further actions
    }

    // Process the successful login
    const { access, refresh } = response.data;

    if (access || refresh) {
      setAuthTokens({ accessToken: access, refreshToken: refresh });
    }

    persistAuthenticatedBackend(authenticatedBaseUrl);
    authDebug("login:success", {
      backend: authenticatedBaseUrl,
      hasAccessToken: Boolean(access),
      hasRefreshToken: Boolean(refresh),
    });

    return {
      ...response.data,
      _apiBaseUrlUsed: authenticatedBaseUrl,
    };

  } catch (error) {
    if (
      error.response?.status === 400 &&
      error.response?.data?.success?.includes("False")
    ) {
      Swal.fire({
        icon: 'warning',
        title: 'License Expired',
        text: 'Your license has been expired. Please renew it to continue using the service. Please contact the administrator, and for more information, check your "Email".',
        confirmButtonText: 'OK',
      });
      return;
    }

    // Show specific error messages based on other API responses or exceptions
    if (
      error.response?.status === 400 &&
      error.response?.data?.email?.includes("Enter a valid email address.")
    ) {
      toast.error("Please enter a valid email address.");
    } else if (
      error.response?.status === 400 &&
      error.response?.data?.non_field_errors?.includes("Invalid credentials")
    ) {
      toast.error("The Entered Email or Password is Incorrect");
    } else if (error.response?.status === 403) {
      toast.error("Access denied. Please contact support.");
    } else if (error.message?.includes("Network Error")) {
      toast.error("Unable to connect to the server. Check your internet connection!");
    } else if (error.response?.status >= 500) {
      toast.error("Server error! Please try again later.");
    } else {
      toast.error(error.response?.data?.message || "An unexpected error occurred. Please try again.");
    }

    clearAuthTokens();
    console.error('Login error:', error.response?.data?.message || "Login failed");
    throw new Error(error.response?.data?.message || "Login failed");
  }
};

export const signupUser = async (formValues) => {
  try {
    const response = await axios.post(`${baseUrl}/signup/`, formValues, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    return response;
  } catch (error) {
    console.error("Error in signupUser:", error);
    throw error;
  }
};

export const fetchLastLogin = async () => {
  try {
    const token = localStorage.getItem('authToken');
    const response = await axios.get(`${baseUrl}/user-last-login/`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      console.error("API Error:", error.response.data);
      throw new Error(error.response.data.detail || "Error fetching last login.");
    } else if (error.request) {
      console.error("Network Error:", error.request);
      throw new Error("Network error. Please try again.");
    } else {
      console.error("Error:", error.message);
      throw new Error("An unexpected error occurred.");
    }
  }
};

export const fetchLoginActivitySummary = async (userId = null) => {
  const token = getAccessToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  const endpoint = userId ? `${baseUrl}/login-activity/${userId}/` : `${baseUrl}/login-activity/`;

  try {
    const response = await axios.get(endpoint, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.data || response.data.status !== "success" || !response.data.data) {
      throw new Error("Login activity returned an unexpected response.");
    }
    return response.data.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || error.message || "Failed to fetch login activity.");
  }
};

export const refreshToken = async () => {
  if (!getRefreshToken()) {
    throw new Error('No refresh token found.');
  }

  try {
    return await requestTokenRefresh();
  } catch (error) {
    console.error('Failed to refresh token:', error.response?.data);
    throw new Error('Failed to refresh token');
  }
};

export const logoutUser = async () => {
  let authToken = getAccessToken();
  const refreshTokenValue = getRefreshToken();

  if (!refreshTokenValue) {
    // Handle missing refresh token
    Swal.fire({
      icon: "error",
      title: "No refresh token found",
      text: "Please log in again to continue.",
    });
    throw new Error("No refresh token found. Please log in again.");
  }

  if (!authToken) {
    console.warn("Auth token missing, trying to refresh token...");
    try {
      authToken = await refreshToken();
      if (!authToken) {
        throw new Error("Unable to refresh token.");
      }
    } catch (error) {
      console.error("Token refresh failed during logout:", error);
      Swal.fire({
        icon: "error",
        title: "Token refresh failed",
        text: "Unable to refresh your session. Please log in again.",
      });
      throw new Error("Token refresh failed. Log in again.");
    }
  }

  // Validate the token if necessary
  if (!isValidToken(authToken)) {
    console.error("Token invalid or expired.");

    // Show SweetAlert for expired token
    Swal.fire({
      icon: "warning",
      title: "Session Expired",
      text: "Your session has been expired. Please log in again to continue.",
      confirmButtonText: "OK",
    }).then((result) => {
      if (result.isConfirmed) {
        // Clear tokens and redirect only after confirmation
        clearAuthTokens();
        window.location.replace("/login");
      }
    });

    return;
  }

  try {
    const response = await axios.post(
      `${baseUrl}/logout/`,
      { refresh_token: refreshTokenValue },
      { headers: { Authorization: `Bearer ${authToken}` } }
    );

    // Clear tokens after successful logout
    clearAuthTokens();

    return response.data; // Return successful logout response
  } catch (error) {
    console.error("Logout Error:", error.response?.data || error.message);

    if (error.response?.data?.error === "Token is blacklisted") {
      Swal.fire({
        icon: "error",
        title: "Blacklisted Token",
        text: "Your token has been blacklisted. Please log in again.",
        confirmButtonText: "OK",
      }).then((result) => {
        if (result.isConfirmed) {
          // Clear tokens and redirect only after confirmation
          clearAuthTokens();
          window.location.replace("/login");
        }
      });
      return;
    }

    // Generic error handling
    Swal.fire({
      icon: "error",
      title: "Logout Failed",
      text: error.response?.data?.message || "An error occurred while logging out.",
    });
    throw new Error(error.response?.data?.message || "Logout failed.");
  }
};

// Utility function to check if token is valid
function isValidToken(token) {
  try {
    const decoded = JSON.parse(atob(token.split(".")[1])); // Decode the JWT
    return decoded.exp * 1000 > Date.now();  // Check if it's expired
  } catch (e) {
    console.error("Token validation failed:", e);
    return false;
  }
}

export const requestPasswordReset = async (email) => {
  try {
    const response = await axios.post(
      `${baseUrl}/password-reset-request/`,
      {
        email: email,
      },
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || "Failed to send reset password link."
    );
  }
};

export const resetPassword = async (
  uidb64,
  token,
  NewPassword,
  ConfirmPassword
) => {
  try {
    const response = await axios.post(
      `${baseUrl}/password-reset-confirm/?uidb64=${uidb64}&token=${token}`,
      {
        uidb64: uidb64,
        token: token,
        NewPassword: NewPassword,
        ConfirmPassword: ConfirmPassword,
      },
      {
        headers: { "Content-Type": "application/json" },
      }
    );

    return response.data;
  } catch (error) {
    const errorMessage =
      error.response?.data?.detail ||
      error.response?.data?.uidb64?.[0] ||
      error.response?.data?.new_password?.[0] ||
      error.response?.data?.confirm_password?.[0] ||
      error.message ||
      "Failed to reset password.";
    throw new Error(errorMessage);
  }
};

export const updateKYC = async (formValues) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const formData = new FormData();

    formData.append('id_proof', formValues.id_proof.toLowerCase().replace(/\s+/g, '_'));

    if (formValues.document_file_front instanceof File) {
      formData.append('document_file_front', formValues.document_file_front);
    }

    if (formValues.document_file_back instanceof File) {
      formData.append('document_file_back', formValues.document_file_back);
    }

    formData.append('address_proof_id', formValues.address_proof_id.toLowerCase().replace(/\s+/g, '_'));

    if (formValues.address_prof_front instanceof File) {
      formData.append('address_prof_front', formValues.address_prof_front);
    }
    if (formValues.address_prof_back instanceof File) {
      formData.append('address_prof_back', formValues.address_prof_back);
    }
    // formData.append('is_verified', false);

    const response = await axios.post(`${baseUrl}/kyc/update/`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || "Failed to update KYC"
    );
  }
};

export const getKYC = async (formValues) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/kyc/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    // showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const verifyOtp = async (email, otp) => {
  try {
    const otpApiBaseUrl =
      (typeof window !== "undefined" ? window.localStorage.getItem("pendingOtpApiBaseUrl") : null) ||
      baseUrl;
    const response = await axios.post(`${otpApiBaseUrl}/verify-otp/`, {
      email: email,
      otp_code: otp
    }, {
      skipAuthRefresh: true,
    });

    if (response.data.access) {
      setAuthTokens({
        accessToken: response.data.access,
        refreshToken: response.data.refresh,
      });
      persistAuthenticatedBackend(otpApiBaseUrl);
      authDebug("otp:success", {
        backend: otpApiBaseUrl,
        hasAccessToken: Boolean(response.data.access),
        hasRefreshToken: Boolean(response.data.refresh),
      });
    }

    return response.data;
  } catch (error) {
    const responseData = error.response?.data;
    const message =
      responseData?.message ||
      responseData?.non_field_errors?.[0] ||
      responseData?.detail ||
      (Array.isArray(responseData) ? responseData[0] : null) ||
      "OTP verification failed. Please try again.";
    throw new Error(message);
  }
};

export const resendOtp = async (email) => {
  try {
    const otpApiBaseUrl =
      (typeof window !== "undefined" ? window.localStorage.getItem("pendingOtpApiBaseUrl") : null) ||
      baseUrl;
    const response = await axios.post(`${otpApiBaseUrl}/resend-otp/`, {
      email: email
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Server Error');
  }
};

export const changePassword = async (oldPassword, newPassword, confirmNewPassword) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.post(`${baseUrl}/change-password/`, {
      OldPassword: oldPassword,
      NewPassword: newPassword,
      ConfirmNewPassword: confirmNewPassword
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to change password";
    if (error.response?.data?.code === "token_not_valid") {
      // Handle token refresh or logout
      alert("Your session has expired. Please log in again.");
      // Optionally redirect to login page
    }
    throw new Error(errorMessage);
  }
};

export const fetchUserProfile = async () => {
  let token = getAccessToken();

  if (!token) {
    handleNoTokenError();
    throw new Error('No authentication token found.');
  }

  try {
    const response = await axios.get(`${baseUrl}/user-profile/`);
    return response.data;
  } catch (error) {
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        try {
          token = await refreshToken();
          const retryResponse = await axios.get(`${baseUrl}/user-profile/`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          return retryResponse.data;
        } catch (refreshError) {
          console.error('Refresh token error:', refreshError);
          handleAuthError();
          throw new Error('Session expired. Please log in again.');
        }
      }
    }

    console.error('Error fetching user profile:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user profile. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user profile');
  }
};

export const updateUserProfile = async (formValues) => {
  const token = getAccessToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.patch(`${baseUrl}/user-profile/`, formValues, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to update user profile";
    if (error.response?.data?.code === "token_not_valid") {
      alert("Your session has expired. Please log in again.");
    }
    throw new Error(errorMessage);
  }
};

export const updateUserProfileImage = async (file) => {

  const formData = new FormData();

  formData.append("profilePicture", file);
  const token = getAccessToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.patch(`${baseUrl}/user-profile/`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to update user profile";
    if (error.response?.data?.code === "token_not_valid") {
      alert("Your session has expired. Please log in again.");
    }
    throw new Error(errorMessage);
  }
};

export const fetchUserData = async (page_number, page_size, formValues) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/users-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size,
        formValues,
      },
    });

    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const fetchSubAdminsList = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/get-subadmins-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const fetchPeddingKycList = async (page_number, page_size, q) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/pending-kyc-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size: page_size,
        q: q
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const getKycViewById = async (id) => {
  console.log("Inside getKycViewById with clientId:", id);

  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-kyc-by-id/${id}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Client response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching getKycViewById by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch getKycViewById by ID.");
  }
};

export const fetchRolesList = async (formValues) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-roles-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: formValues,
    });
    return response.data;

  } catch (error) {
    console.error('Error fetching roles:', error);
    throw error;
  }
};

export const fetchRolePermissions = async (formValues) => {
  try {
    const token = localStorage.getItem('authToken');
    const response = await axios.get(`${baseUrl}/role-permissions/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: formValues,
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching role permissions:', error);
    throw error;
  }
};


export const updateRolePermissions = async (roleId, permissions) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/update-role-permissions/${roleId}/`, permissions, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error updating role permissions:", error);
    throw new Error(error.response?.data?.detail || "Failed to update role permissions.");
  }
};

export const createRole = async (roleData) => {
  const token = getAuthToken();
  console.log("Role Data: ", roleData);


  const response = await fetch(`${baseUrl}/create-roles/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(roleData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`Failed to create role: ${JSON.stringify(errorData)}`);
  }

  const data = await response.json();
  return data;
};


export const deleteRole = async (roleId) => {
  const token = localStorage.getItem('authToken');

  const response = await axios.delete(`${baseUrl}/delete-roles/${roleId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (response.status !== 200) {
    throw new Error('Failed to delete the role');
  }

  return response.data;
};

export const handleApprove = async (kycId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/kyc/verify/${kycId}/`,
      { action: "approve" },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || "Failed to approve KYC");
  }
};

export const handleReject = async (kycId, reason) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(
      `${baseUrl}/kyc/verify/${kycId}/`,
      { action: "reject", reason }, // Add reason to the payload
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || "Failed to reject KYC");
  }
};


export const deleteUser = async (userId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const deleteUrl = `${baseUrl}/delete-user/${userId}/`;
    const response = await axios.delete(deleteUrl, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error(`Error deleting user with ID ${userId}:`, error);
    throw error;
  }
};

export const updateUser = async (userId, data) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(`${baseUrl}/update-user/${userId}/`, data, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || "Failed to update user");
  }
};

export const addUser = async (userData) => {
  const token = getAuthToken();
  console.log('@@@@@@@@@@@@@@@@@@@@', token);

  if (!token) {
    console.log('@@@@@@@@@@@@@@@@@@@@');
    throw new Error("No authentication token found.");

  }

  try {
    const response = await axios.post(`${baseUrl}/create-user/`, userData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    if (error.response?.data?.email) {
      // Extract the email-specific error
      const emailError = error.response.data.email[0];
      console.log('Email Error:', emailError);
      throw new Error(emailError);
    } else if (error.response?.data?.phoneNumber) {
      const phoneError = error.response.data.phoneNumber[0];
      console.log('Phone Number Error:', phoneError);
      throw new Error(phoneError); // Throw phone-specific error
    } else {
      // Handle other general errors
      const errorMessage = error.response?.data?.detail || "Failed to add user";
      console.error('General Error:', errorMessage);
      throw new Error(errorMessage); // Throw a general error if no email error is found
    }
  }
};

export const fetchUserById = async (userId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/user/${userId}/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error(`Error fetching user with ID ${userId}:`, error);
    throw new Error(error.response?.data?.message || "Failed to fetch user data.");
  }
};

export const getSegments = async (page_number, page_size, q) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-segments/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        page_number: page_number,
        page_size: page_size,
        q: q
      }
    });

    console.log("Segments response:", response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getSegmentsList = async () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-segments-list/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Segments response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching segments:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to fetch segments."
    );
  }
};

export const getSubSegment = async (segment) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-sub-segments-by-segment/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: { segment },
    });

    console.log("getSubSegment response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching getSubSegment:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to fetch getSubSegment."
    );
  }
};

export const createSegment = async (segment) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(
      `${baseUrl}/create-segments/`,
      segment,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("Create Segment response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error creating segment:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to create segment."
    );
  }
};

export const updateSegment = async (segment, id) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(
      `${baseUrl}/update-segments/${id}/`,
      segment,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("update Segment response:", response.data);
    return response.data;
  } catch (error) {
    console.error(`Error update Segment with ID ${id}:`, error);
    throw new Error(
      error.response?.data?.detail || "Failed to create update."
    );
  }
};

export const deleteSegment = async (id) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(
      `${baseUrl}/delete-segments/${id}/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data.msg;
  } catch (error) {
    console.error(`Error deleting Segment with ID ${id}:`, error);
    throw new Error(error.response?.data?.detail || "Failed to delete Segment.");
  }
};

export const getServices = async (page_number, page_size, q) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-services/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        page_number: page_number,
        page_size: page_size,
        q: q
      },
    });

    console.log("Service response:", response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getServicesList = async () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-services-list/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Service response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching service:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to fetch service."
    );
  }
};

export const getGroupServices = async (page_number, page_size, q) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-group-service/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        page_number: page_number,
        page_size: page_size,
        q: q
      },
    });

    console.log("GroupServices response:", response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getGroupServicesList = async () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-group-service-list/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("GroupServices response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching GroupServices:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to fetch GroupServices."
    );
  }
};

export const getGroupServiceById = async (id) => {
  if (!id) throw new Error("ID is required for fetching service details.");

  const token = localStorage.getItem("authToken");
  if (!token) throw new Error("No authentication token found.");

  try {
    const response = await axios.get(`${baseUrl}/get-Groupservices-by-id/${id}/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("Group Service response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching Group Service by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch Group Service by ID.");
  }
};


export const getGroupServiceQtyDetails = async (id) => {
  if (!id) throw new Error("ID is required for fetching service details.");

  const token = localStorage.getItem("authToken");
  if (!token) throw new Error("No authentication token found.");

  try {
    const response = await axios.get(`${baseUrl}/get-services-Qty_details/${id}/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("GroupServiceQtyDetails response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching GroupServiceQtyDetails by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch GroupServiceQtyDetails by ID.");
  }
};

export const getClientGroupService = async (id) => {
  if (!id) throw new Error("ID is required for fetching service details.");

  const token = localStorage.getItem("authToken");
  if (!token) throw new Error("No authentication token found.");

  try {
    const response = await axios.get(`${baseUrl}/clients-by-group-service/${id}/`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("getClientGroupService response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching getClientGroupService by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch getClientGroupService by ID.");
  }
};

export const addGroupService = async (groupData) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/create-group-service/`, groupData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log("Add Group Service:", response)
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to add Group Service";
    throw new Error(errorMessage);
  }
};

export const updateGroupService = async (id, groupData) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(`${baseUrl}/update-group-service/${id}/`, groupData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log("Update Group Service:", response);
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to Update Group Service";
    throw new Error(errorMessage);
  }
};


export const deleteGroupServices = async (id) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(
      `${baseUrl}/delete-group-service/${id}/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data.msg;
  } catch (error) {
    console.error(`Error deleting delete group with ID ${id}:`, error);
    throw new Error(error.response?.data?.detail || "Failed to delete delete group.");
  }
};

export const createServices = async (segment) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(
      `${baseUrl}/create-services/`,
      segment,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("Create Service response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error creating service:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to create service."
    );
  }
};

export const updateServices = async (id, data) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(`${baseUrl}/update-services/${id}/`, data, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error(`Error updating service with ID ${id}:`, error);
    throw new Error(error.response?.data?.message || "Failed to update service.");
  }
};

export const deleteServices = async (id) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(
      `${baseUrl}/delete-services/${id}/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data.msg;
  } catch (error) {
    console.error(`Error deleting service with ID ${id}:`, error);
    throw new Error(error.response?.data?.detail || "Failed to delete service.");
  }
};

export const deleteStrategies = async (id) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(
      `${baseUrl}/delete-strategies/${id}/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data.msg;
  } catch (error) {
    console.error(`Error deleting strategies with ID ${id}:`, error);
    throw new Error(error.response?.data?.detail || "Failed to delete strategies.");
  }
};

export const getCategories = async (page_number, page_size, q) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-category/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size: page_size,
        q: q
      },
    });
    console.log('Fetched categories:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getCategoriesList = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-category-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('Fetched categories:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw new Error(error.response?.data?.message || "Failed to fetch categories.");
  }
};

export const addCategory = async (category) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/create-category/`, category, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log("Add Category:", response)
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to add category";
    throw new Error(errorMessage);
  }
};

export const updateCategory = async (category, id) => {
  console.log("Category Data: ", category);
  console.log("Category ID: ", id);
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(`${baseUrl}/update-category/${id}/`, category, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || "Failed to update user");
  }
};

export const deleteCategory = async (categoryId) => {

  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const deleteUrl = `${baseUrl}/delete-category/${categoryId}/`;
    const response = await axios.delete(deleteUrl, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.data;
  }
  catch (error) {
    console.error(`Error deleting category with ID ${categoryId}:`, error);
    throw error;
  }
};

export const getStrategies = async (page_number, page_size) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-strategies/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        page_number: page_number,
        page_size: page_size
      },
    });

    console.log("strategies response:", response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const updateStrategy = async (id, strategyData) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(`${baseUrl}/update-strategies/${id}/`, strategyData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error updating strategy:", error);
    throw new Error(error.response?.data?.detail || "Failed to update strategy.");
  }
};

export const createStrategy = async (strategyData) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/add-strategies/`, strategyData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error create strategy:", error);
    throw new Error(error.response?.data?.detail || "Failed to create strategy.");
  }
};

export const getStrategyById = async (id) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-strategies-by-id/${id}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Strategy response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching strategy by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch strategy by ID.");
  }
};

export const getStrategyClient = async (id) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-strategies-client/${id}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Strategy response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching strategy client by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch strategy client by ID.");
  }
};

export const getStrategyClientList = async (id) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-strategies-by-id/${id}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Strategy response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching strategy client by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch strategy client by ID.");
  }
};

export const updateStrategyClientList = async (id, selectedClients) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(
      `${baseUrl}/assign-client-to-strategy/${id}/`,
      { clients: selectedClients },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("Update response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error updating strategy client list:", error);
    throw new Error(error.response?.data?.detail || "Failed to update strategy client list.");
  }
};


export const getLicence = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-License/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    // console.log('getLicence:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getLicence:', error);
    throw new Error(error.response?.data?.message || "Failed to getLicence.");
  }
};

// Add License
export const addLicense = async (licences) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/create-License/`, licences, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    // console.log("Add Category:",response)
    console.log("Add Services:", response)
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to add services";
    throw new Error(errorMessage);
  }
};

// update License
export const updateLicense = async (licences, id) => {
  console.log("Licence Data: ", licences);
  console.log("Licence ID: ", id);
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.put(`${baseUrl}/update-License/${id}/`, licences, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error(`Error updating license with ID ${id}:`, error);
    throw new Error(error.response?.data?.message || "Failed to update user");
  }
};

export const deleteLicense = async (id) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(
      `${baseUrl}/update-License/${id}/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data.msg;
  } catch (error) {
    console.error(`Error deleting Licence with ID ${id}:`, error);
    throw new Error(error.response?.data?.detail || "Failed to delete Licence.");
  }
};

export const getBroker = async () => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-broker/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('Fetched Broker:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const addBroker = async (category) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/add-broker/`, category, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log("Add broker:", response)
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to add broker";
    throw new Error(errorMessage);
  }
};


export const updateBroker = async (broker, id) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(
      `${baseUrl}/update-broker/${id}/`,
      broker,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("update broker response:", response.data);
    return response.data;
  } catch (error) {
    console.error(`Error update broker with ID ${id}:`, error);
    throw new Error(
      error.response?.data?.detail || "Failed to update broker."
    );
  }
};

export const deleteBroker = async (brokerId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(
      `${baseUrl}/delete-broker/${brokerId}/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data.msg;
  } catch (error) {
    console.error(`Error deleting broker with ID ${brokerId}:`, error);
    throw new Error(error.response?.data?.detail || "Failed to delete broker.");
  }
};

export const getClients = async (page_number, page_size) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size
      },
    });
    console.log('Fetched Clients:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getExpiredClients = async (page_number, page_size) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/expiry-clients-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size
      },
    });
    console.log('Expired Fetched Clients:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const deleteClient = async (clientId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(
      `${baseUrl}/delete-client/${clientId}/`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data.msg;
  } catch (error) {
    console.error(`Error deleting Client with ID ${clientId}:`, error);
    throw new Error(error.response?.data?.detail || "Failed to delete Client.");
  }
};

export const addClient = async (client) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/create-client/`, client, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log("Add client:", response)
    return response.data;
  } catch (error) {
    const responseData = error.response?.data || {};
    const nestedErrors = responseData.errors || {};

    if (responseData.email || nestedErrors.email) {
      const emailError = (responseData.email || nestedErrors.email)[0];
      console.log('Email Error:', emailError);
      throw new Error(emailError);
    } else if (responseData.phoneNumber || nestedErrors.phoneNumber) {
      const phoneError = (responseData.phoneNumber || nestedErrors.phoneNumber)[0];
      console.log('Phone Number Error:', phoneError);
      throw new Error(phoneError);
    } else {
      const firstFieldError = Object.values(nestedErrors).find(
        (value) => Array.isArray(value) && value.length
      );
      const errorMessage =
        responseData.detail ||
        (Array.isArray(firstFieldError) ? firstFieldError[0] : null) ||
        "Failed to add client";
      throw new Error(errorMessage);
    }
  }
};

export const getClientById = async (clientId) => {
  console.log("Inside getClientById with clientId:", clientId);

  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-by-id/${clientId}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Client response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching client by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch client by ID.");
  }
};

export const getStrategiesById = async (id) => {
  console.log(`Fetching client list for strategy ID: ${id}`);

  const token = localStorage.getItem("authToken");
  console.log(token, 'tokentokentokentoken');

  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(
      `${baseUrl}/strategies/${id}/clients/`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    console.log("Client response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching client list in strategies:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch client list in strategies.");
  }
};



export const getActiveInactiveClient = async (userId) => {
  console.log("Inside getActiveInactiveClient with clientId:", userId);

  const token = localStorage.getItem("authToken");
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/active-inactive-clients/${userId}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Client response:", response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const updateClient = async (id, data) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(
      `${baseUrl}/update-client/${id}/`,
      data,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("update client response:", response.data);
    return response.data;
  } catch (error) {
    console.error(`Error update client with ID ${id}:`, error);
    throw new Error(
      error.response?.data?.detail || "Failed to update client."
    );
  }
};

export const updateClientStatus = async (id, data) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(
      `${baseUrl}/update-client-status/${id}/`,
      data,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("updateClientStatus response:", response.data);
    return response.data;
  } catch (error) {
    console.error(`Error updateClientStatus with ID ${id}:`, error);
    throw new Error(
      error.response?.data?.detail || "Failed to updateClientStatus."
    );
  }
};

export const getClientSegmentsList = async (segment = "") => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-segments-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: segment ? { segment } : {},
    });

    console.log("Fetched Client Segments List:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching Client Segments List:", error);
    throw new Error(error.response?.data?.message || "Failed to fetch Client Segments List.");
  }
};

export const getExpiryDate = async (symbol) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-expiry-date-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: { symbol },
    });

    console.log("Fetched getExpiryDate List:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching getExpiryDate:", error);
    throw new Error(error.response?.data?.message || "Failed to fetch getExpiryDate.");
  }
};

export const getClientTradeSetting = async (clientId, segmentId, subSegmentId) => {
  const token = getAuthToken();
  console.log(`clientid: ${clientId}, segmentid: ${segmentId}, subsegmentid: ${subSegmentId}`);

  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {

    const response = await axios.get(`${baseUrl}/get-client-trade-setting/?client=${clientId}&segment=${segmentId}&sub_segment=${subSegmentId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },

    });

    console.log("Fetched Client Trade Setting:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching Client Trade Setting:", error);
    throw new Error(error.response?.data?.message || "Failed to fetch Client Trade Setting.");
  }
};

export const getClientMultiLegSettings = async (params = {}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/client-multi-leg-settings/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      params,
    });

    return response.data;
  } catch (error) {
    console.error("Error fetching client multi leg settings:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch client multi leg settings.");
  }
};

export const updateClientMultiLegSetting = async (payload) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(`${baseUrl}/client-multi-leg-settings/`, payload, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error updating client multi leg setting:", error);
    const responseData = error.response?.data;
    const fieldErrors = responseData && typeof responseData === "object"
      ? Object.entries(responseData)
          .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(", ") : messages}`)
          .join("\n")
      : "";
    throw new Error(responseData?.detail || fieldErrors || "Failed to update client multi leg setting.");
  }
};

export const updateClientMultiLegTradeStatus = async (payload) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.patch(`${baseUrl}/client-multi-leg-settings/`, payload, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    return response.data;
  } catch (error) {
    console.error("Error updating multi leg trade status:", error);
    throw new Error(error.response?.data?.detail || "Failed to update multi leg trade status.");
  }
};

export const clearClientMultiLegSetting = async (strategyId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(`${baseUrl}/client-multi-leg-settings/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      params: { strategy: strategyId },
    });
    return response.data;
  } catch (error) {
    console.error("Error clearing client multi leg setting:", error);
    throw new Error(error.response?.data?.detail || "Failed to clear client multi leg setting.");
  }
};

export const executeMultiLegStrategy = async (payload) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/strategies/multileg/execute/`, payload, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error executing multi leg strategy:", error);
    throw new Error(error.response?.data?.detail || "Failed to execute multi leg strategy.");
  }
};

export const getActiveMultiLegStrategies = async (params = {}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/strategies/multileg/active/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      params,
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching active multi leg strategies:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch active multi leg strategies.");
  }
};

export const getMultiLegStrategyDetail = async (executionId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/strategies/multileg/${executionId}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching multi leg strategy detail:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch multi leg strategy detail.");
  }
};

export const exitMultiLegStrategy = async (executionId, payload = {}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/strategies/multileg/${executionId}/exit/`, payload, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error exiting multi leg strategy:", error);
    throw new Error(error.response?.data?.detail || "Failed to exit multi leg strategy.");
  }
};

export const killSwitchMultiLegStrategies = async (payload = {}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/strategies/multileg/kill-switch/`, payload, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error running multi leg kill switch:", error);
    throw new Error(error.response?.data?.detail || "Failed to run multi leg kill switch.");
  }
};

export const killSwitchAllClientTrades = async (payload = {}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/client/kill-switch/`, payload, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error running client global kill switch:", error);
    throw new Error(error.response?.data?.detail || "Failed to run client kill switch.");
  }
};

export const getMultiLegStrategyLogs = async (executionId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/strategies/multileg/${executionId}/logs/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching multi leg strategy logs:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch multi leg strategy logs.");
  }
};

export const getWebhookDiagnostics = async (params = {}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/webhook-diagnostics/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      params,
    });

    return response.data;
  } catch (error) {
    console.error("Error fetching webhook diagnostics:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch webhook diagnostics.");
  }
};

export const getSLTPWatcherStatus = async (params = {}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/sl-tp-watcher/scan/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      params,
    });

    return response.data;
  } catch (error) {
    console.error("Error fetching SL/TP watcher status:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch SL/TP watcher status.");
  }
};

export const getSpecificDetails = async () => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-details/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('getClientDetails:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const updateTradeClient = async (clientId, payload) => {
  console.log('Client ID:', clientId);
  // console.log('Payload:', payload);

  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(
      `${baseUrl}/client-trade-settings/update/`,
      payload,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("Update client response:", response.data);
    return response.data;
  } catch (error) {
    console.error(`Error updating client:`, error.response);
    throw new Error(
      error.response?.data?.detail || "Failed to update client."
    );
  }
};


export const updateTradeStatus = async (formValues) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.patch(`${baseUrl}/update-trade-status/`, formValues, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to update trade status";
    if (error.response?.data?.code === "token_not_valid") {
      alert("Your session has expired. Please log in again.");
    }
    throw new Error(errorMessage);
  }
};

export const getCityData = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-city-data/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('Fetched City:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching City:', error);
    throw new Error(error.response?.data?.message || "Failed to fetch City.");
  }
};

export const getStateData = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-state-data/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('Fetched State:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching State:', error);
    throw new Error(error.response?.data?.message || "Failed to fetch State.");
  }
};

export const searchCity = async (city) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/cities/search/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: { city }, // Adding the query parameter
    });
    console.log('City Search Results:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error searching City:', error);
    throw new Error(error.response?.data?.message || "Failed to search City.");
  }
};

export const searchState = async (state) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/state/search/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: { state }, // Adding the query parameter
    });
    console.log('State Search Results:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error searching State:', error);
    throw new Error(error.response?.data?.message || "Failed to search State.");
  }
};

export const updateAddress = async (formValues) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.patch(`${baseUrl}/user-profile/`, formValues, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to update user profile";
    if (error.response?.data?.code === "token_not_valid") {
      alert("Your session has expired. Please log in again.");
    }
    throw new Error(errorMessage);
  }
};

export const getSubAdmins = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/all-subadmins-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('getSubAdmins:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getSubAdmins:', error);
    throw new Error(error.response?.data?.message || "Failed to getSubAdmins.");
  }
};

export const getInactiveClient = async (page_number, page_size) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/inactive-client-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size
      },
    });
    console.log('getInactiveClient:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getActiveClient = async (page_number, page_size) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/active-client-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size: page_size
      },
    });
    console.log('getActiveClient:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const EnableDisableBroker = async (data) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  const candidateBaseUrls = getBackendCandidateBaseUrls({ preferBrokerBackend: true });
  let lastError = null;

  for (const candidateBaseUrl of candidateBaseUrls) {
    try {
      let candidateToken = getAuthToken() || token;
      const executeRequest = async (authToken) => axios.put(`${candidateBaseUrl}/enable-disable-broker/`, data, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        skipAuthRefresh: true,
      });

      let response;
      try {
        response = await executeRequest(candidateToken);
      } catch (candidateError) {
        if (candidateError.response?.status === 401 && getRefreshToken()) {
          candidateToken = await refreshForBackendCandidate(candidateBaseUrl);
          response = await executeRequest(candidateToken);
        } else {
          throw candidateError;
        }
      }

      console.log(response.data, "EnableDisableBroker");
      persistBrokerBackend(candidateBaseUrl);
      persistAuthenticatedBackend(candidateBaseUrl);
      authDebug("broker-toggle:success", {
        backend: candidateBaseUrl,
      });
      return response.data;
    } catch (candidateError) {
      authDebug("broker-toggle:failure", {
        backend: candidateBaseUrl,
        status: candidateError?.response?.status || null,
      });
      lastError = candidateError;
      if (candidateError?.response?.status === 404) {
        continue;
      }
    }
  }

  const errorMessage = lastError?.response?.data?.detail || lastError?.response?.data?.message || "Failed to update user profile";
  if (lastError?.response?.data?.code === "token_not_valid") {
    alert("Your session has expired. Please log in again.");
  }
  throw new Error(errorMessage);
};

export const UpdateClientBroker = async (data) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  const normalizeBrokerResponse = (payload) => {
    if (!payload || typeof payload !== "object") {
      return null;
    }

    const hasExplicitSuccess = payload.status === "success";
    const hasLegacySuccess = typeof payload.message === "string" && payload.message.toLowerCase().includes("success");
    const hasBrokerData = payload.data && typeof payload.data === "object";

    if (!hasExplicitSuccess && !hasLegacySuccess && !hasBrokerData) {
      return null;
    }

    return {
      status: hasExplicitSuccess ? "success" : "success",
      message: payload.message || "Broker details updated successfully!",
      data: hasBrokerData ? payload.data : {},
    };
  };

  const buildBrokerErrorMessage = (error) => {
    const responseData = error.response?.data;
    if (!responseData) {
      return "Failed to update broker details.";
    }

    if (typeof responseData.message === "string" && responseData.message.trim()) {
      if (responseData.errors && typeof responseData.errors === "object") {
        const fieldErrors = Object.entries(responseData.errors)
          .flatMap(([field, messages]) => {
            if (Array.isArray(messages)) {
              return messages.map((message) => `${field}: ${message}`);
            }
            return [`${field}: ${String(messages)}`];
          });
        if (fieldErrors.length) {
          return `${responseData.message} ${fieldErrors.join(" | ")}`;
        }
      }
      return responseData.message;
    }

    if (typeof responseData.detail === "string" && responseData.detail.trim()) {
      return responseData.detail;
    }

    return "Failed to update broker details.";
  };

  const candidateBaseUrls = getBackendCandidateBaseUrls({ preferBrokerBackend: true });
  let lastError = null;

  for (const candidateBaseUrl of candidateBaseUrls) {
    try {
      let candidateToken = getAuthToken() || token;
      const executeRequest = async (authToken) => axios.put(`${candidateBaseUrl}/update-client-broker/`, data, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        skipAuthRefresh: true,
      });

      let response;
      try {
        response = await executeRequest(candidateToken);
      } catch (candidateError) {
        if (candidateError.response?.status === 401 && getRefreshToken()) {
          candidateToken = await refreshForBackendCandidate(candidateBaseUrl);
          response = await executeRequest(candidateToken);
        } else {
          throw candidateError;
        }
      }

      console.log(response.data, "UpdateClientBroker");
      const normalizedResponse = normalizeBrokerResponse(response.data);
      if (!normalizedResponse) {
        throw new Error("Broker update returned an unexpected response.");
      }

      persistBrokerBackend(candidateBaseUrl);
      persistAuthenticatedBackend(candidateBaseUrl);
      authDebug("broker-save:success", {
        backend: candidateBaseUrl,
        selectedBroker: normalizedResponse?.data?.selected_broker_name || null,
      });
      return normalizedResponse;
    } catch (candidateError) {
      authDebug("broker-save:failure", {
        backend: candidateBaseUrl,
        status: candidateError?.response?.status || null,
      });
      lastError = candidateError;
      if (candidateError?.response?.status === 404) {
        continue;
      }
    }
  }

  const errorMessage = lastError instanceof Error && !lastError?.response ? lastError.message : buildBrokerErrorMessage(lastError);
  if (lastError?.response?.data?.code === "token_not_valid") {
    alert("Your session has expired. Please log in again.");
  }
  throw new Error(errorMessage);
};

export const getClientApiStatus = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-api-status/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('getClientApiStatus:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getClientApiStatus:', error);
    throw new Error(error.response?.data?.message || "Failed to getClientApiStatus.");
  }
};

export const getClientApiStatusById = async (clientId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-broker-status-by-id/${clientId}/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('getClientApiStatus:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getClientApiStatus:', error);
    throw new Error(error.response?.data?.message || "Failed to getClientApiStatus.");
  }
};

export const getClientBrokerDetailsById = async (clientId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-broker-details-by-id/${clientId}/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('getClientBrokerDetailsById:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getClientBrokerDetailsById:', error);
    throw new Error(error.response?.data?.message || "Failed to getClientBrokerDetailsById.");
  }
};

export const getBrokerLoginActivity = async (clientId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/broker-log-activity/${clientId}/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('getBrokerLoginActivity:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getBrokerLoginActivity:', error);
    throw new Error(error.response?.data?.message || "Failed to getBrokerLoginActivity.");
  }
};

export const getClientBrokerLoginActivity = async (clientId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/user-broker-log/${clientId}/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('getClientBrokerLoginActivity:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getClientBrokerLoginActivity:', error);
    throw new Error(error.response?.data?.message || "Failed to getClientBrokerLoginActivity.");
  }
};

export const getClientBrokerDetail = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  const candidateBaseUrls = getBackendCandidateBaseUrls({ preferBrokerBackend: true });
  let lastError = null;

  for (const candidateBaseUrl of candidateBaseUrls) {
    try {
      let candidateToken = getAuthToken() || token;
      const executeRequest = async (authToken) => axios.get(`${candidateBaseUrl}/get-client-broker-details/`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        skipAuthRefresh: true,
      });

      let response;
      try {
        response = await executeRequest(candidateToken);
      } catch (candidateError) {
        if (candidateError.response?.status === 401 && getRefreshToken()) {
          candidateToken = await refreshForBackendCandidate(candidateBaseUrl);
          response = await executeRequest(candidateToken);
        } else {
          throw candidateError;
        }
      }

      console.log('getClientBrokerDetail', response.data);
      const payload = response.data;
      const normalizedResponse =
        payload && typeof payload === "object" && payload.data && typeof payload.data === "object"
          ? {
              status: payload.status || "success",
              data: payload.data,
              message: payload.message || null,
            }
          : null;

      if (!normalizedResponse) {
        throw new Error("Broker details returned an unexpected response.");
      }

      authDebug("broker-details:success", {
        backend: candidateBaseUrl,
        selectedBroker: normalizedResponse?.data?.selected_broker_name || null,
      });
      return normalizedResponse;
    } catch (error) {
      lastError = error;
    }
  }

  console.error('Error getClientBrokerDetail:', lastError);
  throw new Error(lastError?.response?.data?.message || lastError?.message || "Failed to getClientBrokerDetail.");
};

export const getAngelOneSettings = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/angelone/settings/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error getAngelOneSettings:", error);
    throw new Error(error.response?.data?.message || "Failed to fetch Angel One settings.");
  }
};

export const getAngelOneTokenStatus = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/angelone/token-status/`, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.data || response.data.status !== "success" || !response.data.data) {
      throw new Error("Angel One token status returned an unexpected response.");
    }
    return response.data.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || error.message || "Failed to fetch Angel One token status.");
  }
};

const getBackendCandidateBaseUrls = ({ preferBrokerBackend = false } = {}) => {
  const browserHost = typeof window !== "undefined" ? window.location.hostname : "";
  const isLocalLikeHost =
    browserHost === "0.0.0.0" ||
    /^192\.168\./.test(browserHost) ||
    /^10\./.test(browserHost) ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(browserHost);

  const localBaseUrl = getLocalApiBaseUrl();
  const normalizedBaseUrl = baseUrl.replace(/\/$/, "");
  const authenticatedBaseUrl = (getAuthenticatedApiBaseUrl() || "").replace(/\/$/, "");
  const brokerBaseUrl = (getBrokerApiBaseUrl() || "").replace(/\/$/, "");

  const prioritizedBaseUrls = preferBrokerBackend
    ? [brokerBaseUrl, authenticatedBaseUrl, normalizedBaseUrl]
    : [authenticatedBaseUrl, brokerBaseUrl, normalizedBaseUrl];

  return (isLocalLikeHost
    ? [...prioritizedBaseUrls, localBaseUrl]
    : prioritizedBaseUrls
  ).filter(Boolean).filter(
    (value, index, array) =>
      array.findIndex((item) => item.replace(/\/$/, "") === value.replace(/\/$/, "")) === index,
  );
};

const refreshForBackendCandidate = async (targetBaseUrl) => {
  const storedRefreshToken = getRefreshToken();
  if (!storedRefreshToken) {
    throw new Error("No refresh token found.");
  }

  const response = await axios.post(
    `${targetBaseUrl}/token/refresh/`,
    { refresh: storedRefreshToken },
    { skipAuthRefresh: true },
  );
  const nextAccessToken = response?.data?.access;
  const nextRefreshToken = response?.data?.refresh || storedRefreshToken;
  if (!nextAccessToken) {
    throw new Error("Token refresh did not return a new access token.");
  }
  setAuthTokens({ accessToken: nextAccessToken, refreshToken: nextRefreshToken });
  persistAuthenticatedBackend(targetBaseUrl);
  authDebug("refresh:candidate-success", {
    backend: targetBaseUrl,
    rotatedRefreshToken: Boolean(response?.data?.refresh),
  });
  return nextAccessToken;
};

const requestBrokerRuntimeEndpoint = async ({
  method = "get",
  path,
  data,
  expectedData = false,
  unexpectedResponseMessage,
}) => {
  const initialAccessToken = getAuthToken();
  if (!initialAccessToken) {
    throw new Error("No authentication token found.");
  }

  const candidateBaseUrls = getBackendCandidateBaseUrls({ preferBrokerBackend: true });
  let lastError = null;

  for (const candidateBaseUrl of candidateBaseUrls) {
    try {
      let candidateToken = getAuthToken() || initialAccessToken;
      const executeRequest = async (authToken) => axios({
        method,
        url: `${candidateBaseUrl}${path}`,
        data,
        headers: {
          Authorization: `Bearer ${authToken}`,
          "Content-Type": "application/json",
        },
        skipAuthRefresh: true,
      });
      authDebug("broker-runtime:attempt", {
        backend: candidateBaseUrl,
        path,
        method: method.toUpperCase(),
        hasAccessToken: Boolean(candidateToken),
      });

      let response;
      try {
        response = await executeRequest(candidateToken);
      } catch (candidateError) {
        if (candidateError.response?.status === 401 && getRefreshToken()) {
          candidateToken = await refreshForBackendCandidate(candidateBaseUrl);
          response = await executeRequest(candidateToken);
        } else {
          throw candidateError;
        }
      }

      const payload = response?.data;
      const isValidPayload = expectedData
        ? payload && payload.status === "success" && payload.data
        : payload && payload.status;

      if (!isValidPayload) {
        throw new Error(unexpectedResponseMessage);
      }

      authDebug("broker-runtime:success", {
        backend: candidateBaseUrl,
        path,
        method: method.toUpperCase(),
      });
      return payload;
    } catch (candidateError) {
      authDebug("broker-runtime:failure", {
        backend: candidateBaseUrl,
        path,
        method: method.toUpperCase(),
        status: candidateError?.response?.status || null,
      });
      lastError = candidateError;
      if (candidateError.response?.status === 404) {
        continue;
      }
    }
  }

  throw lastError || new Error(unexpectedResponseMessage);
};

export const getBrokerRuntimeStatus = async () => {
  try {
    const payload = await requestBrokerRuntimeEndpoint({
      method: "get",
      path: "/broker-runtime-status/",
      expectedData: true,
      unexpectedResponseMessage: "Broker runtime status returned an unexpected response.",
    });
    return payload.data;
  } catch (error) {
    if (error.response?.status === 404) {
      try {
        const angelOneStatus = await getAngelOneTokenStatus();
        return {
          session: {
            status: angelOneStatus.session_status || (angelOneStatus.session_active ? "active" : "inactive"),
            is_active: Boolean(angelOneStatus.session_active),
            last_activity_at: angelOneStatus.last_activity_at || null,
            validated_at: angelOneStatus.validated_at || null,
          },
          token: {
            status: angelOneStatus.token_status || (angelOneStatus.is_expired ? "expired" : angelOneStatus.access_token ? "active" : "unavailable"),
            is_active: Boolean(!angelOneStatus.is_expired && angelOneStatus.access_token),
            is_expired: Boolean(angelOneStatus.is_expired),
            expires_at: angelOneStatus.expires_at || angelOneStatus.access_token_expiry || null,
          },
          last_login_at: angelOneStatus.last_login_at || angelOneStatus.tokenCreatedAt || null,
          last_logout_at: angelOneStatus.last_logout_at || null,
          auth_mode: "direct_credentials",
          connect_action_label: "Generate Angel One Token",
          save_action_label: "Save Angel One Credentials",
        };
      } catch (fallbackError) {
        throw new Error(fallbackError.response?.data?.message || fallbackError.message || "Failed to fetch broker runtime status.");
      }
    }
    throw new Error(error.response?.data?.message || error.message || "Failed to fetch broker runtime status.");
  }
};

export const generateBrokerToken = async () => {
  try {
    return await requestBrokerRuntimeEndpoint({
      method: "post",
      path: "/broker-generate-token/",
      data: {},
      expectedData: false,
      unexpectedResponseMessage: "Broker token generation returned an unexpected response.",
    });
  } catch (error) {
    if (error.response?.status === 404 || error.response?.status === 500 || error.response?.status === 503) {
      const connectResponse = await startBrokerConnectFlow("/broker_auth_login/?broker=angel%20one");
      return {
        status: "success",
        action: "redirect",
        message: "Broker login requires redirect flow on this backend.",
        redirect_url: connectResponse.redirect_url,
      };
    }
    throw new Error(error.response?.data?.message || error.message || "Failed to generate broker token.");
  }
};

export const updateAngelOneSettings = async (data) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.patch(`${baseUrl}/angelone/settings/`, data, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error updateAngelOneSettings:", error);
    throw new Error(error.response?.data?.message || "Failed to update Angel One settings.");
  }
};

export const getClientTradeStatus = async (page_number, page_size, q) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-Trade-status/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size: page_size,
        q: q
      },
    });
    console.log('getClientTradeStatus:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getTradeHistory = async (page_number, page_size, fromDate, toDate, broker, orderStatus, indexSymbol, strategy, q) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-trade-history/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size,
        from_date: fromDate,
        to_date: toDate,
        broker: broker,
        order_status: orderStatus,
        Index_symbol: indexSymbol,
        strategy: strategy,
        q: q
      },
    });
    console.log('getTradeHistory:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    // showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getCompleteTrade = async (page_number, page_size, fromDate, toDate, broker, orderStatus, indexSymbol, strategy, q) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/client-complete-trade-history/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size,
        from_date: fromDate,
        to_date: toDate,
        broker: broker,
        order_status: orderStatus,
        Index_symbol: indexSymbol,
        strategy: strategy,
        q: q
      },
    });
    console.log('getCompleteTrade:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    // showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const getClientTradeHistory = async (page_number, page_size, fromDate, toDate, broker, orderStatus, indexSymbol, strategy, q) => {
  const token = getAuthToken();
  if (!token) {
    handleNoTokenError();
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-client-trade-history/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_number: page_number,
        page_size,
        from_date: fromDate,
        to_date: toDate,
        broker: broker,
        order_status: orderStatus,
        Index_Symbol: indexSymbol,
        strategy: strategy,
        q: q
      },
    });
    console.log('getClientTradeHistory:', response.data);
    return response.data;
  } catch (error) {
    // Check for specific errors related to expired or invalid tokens
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        handleAuthError(); // Call this to handle expired session/token
        throw new Error('Session expired. Please log in again.');
      }
    }

    console.error('Error fetching user data:', error);
    // showAlert('error', 'Error', error.response?.data?.detail || 'Failed to fetch user data. Please try again later.');
    throw new Error(error.response?.data?.detail || 'Failed to fetch user data');
  }
};

export const updateClientTradeStatus = async (id, data) => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.patch(
      `${baseUrl}/client/${id}/update-trade-status/`,
      data,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("updateClientTradeStatus response:", response.data);
    return response.data;
  } catch (error) {
    console.error(`Error updateClientTradeStatus with ID ${id}:`, error);
    throw new Error(
      error.response?.data?.detail || "Failed to updateClientTradeStatus."
    );
  }
};

export const getClientsFilter = async (clientType, tradingType, page_size) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/clients-filter/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        client_type: clientType,
        trading_type: tradingType,
        page_size
      },
    });
    console.log('getClientsFilter:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getClientsFilter:', error);
    throw new Error(error.response?.data?.message || "Failed to fetch client filter data.");
  }
};

export const BrokerAuthLogin = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/broker_auth_login/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('BrokerAuthLogin:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error BrokerAuthLogin:', error);
    throw new Error(error.response?.data?.message || "Failed to BrokerAuthLogin.");
  }
};

export const startBrokerConnectFlow = async (connectPath) => {
  const initialAccessToken = getAuthToken();
  if (!initialAccessToken) {
    throw new Error("No authentication token found.");
  }
  const storedRefreshToken = getRefreshToken();
  if (!connectPath) {
    throw new Error("Selected broker does not support panel-driven login.");
  }

  const isLegacyAngelOneRedirect = (redirectUrl) => {
    if (!redirectUrl) {
      return false;
    }
    return (
      redirectUrl.includes("smartapi.angelbroking.com/publisher-login") ||
      redirectUrl.includes("state=example_state")
    );
  };

  const requestConnect = async (targetBaseUrl, authToken) => {
    const requestedUrl = new URL(`${targetBaseUrl}${connectPath}`, window.location.origin).href;
    authDebug("broker-connect:attempt", {
      backend: targetBaseUrl,
      connectPath,
      hasAccessToken: Boolean(authToken),
    });
    const response = await axios.get(`${targetBaseUrl}${connectPath}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      skipAuthRefresh: true,
      maxRedirects: 0,
      validateStatus: (statusCode) => statusCode >= 200 && statusCode < 400,
    });

    if (response.data?.redirect_url) {
      return response.data.redirect_url;
    }

    if (typeof response.headers?.location === 'string') {
      return response.headers.location;
    }

    if (response.request?.responseURL && response.request.responseURL !== requestedUrl) {
      return response.request.responseURL;
    }

    return null;
  };

  const extractErrorMessage = (error) =>
    error?.response?.data?.message ||
    error?.response?.data?.error ||
    error?.message ||
    "Failed to start broker connect flow.";

  const refreshForBackend = async (targetBaseUrl) => {
    if (!storedRefreshToken) {
      throw new Error("No refresh token found.");
    }

    const response = await axios.post(
      `${targetBaseUrl}/token/refresh/`,
      { refresh: storedRefreshToken },
      { skipAuthRefresh: true },
    );
    const nextAccessToken = response?.data?.access;
    const nextRefreshToken = response?.data?.refresh || storedRefreshToken;
    if (!nextAccessToken) {
      throw new Error("Token refresh did not return a new access token.");
    }
    setAuthTokens({ accessToken: nextAccessToken, refreshToken: nextRefreshToken });
    persistAuthenticatedBackend(targetBaseUrl);
    authDebug("broker-connect:refresh-success", {
      backend: targetBaseUrl,
      rotatedRefreshToken: Boolean(response?.data?.refresh),
    });
    return nextAccessToken;
  };

  try {
    const browserHost = typeof window !== "undefined" ? window.location.hostname : "";
    const isLocalLikeHost =
      browserHost === "0.0.0.0" ||
      /^192\.168\./.test(browserHost) ||
      /^10\./.test(browserHost) ||
      /^172\.(1[6-9]|2\d|3[0-1])\./.test(browserHost);

    const localBaseUrl = getLocalApiBaseUrl();
    const normalizedConnectPath = String(connectPath || "");
    const isAngelOneBrokerConnect =
      normalizedConnectPath.includes("/broker_auth_login/") &&
      normalizedConnectPath.toLowerCase().includes("broker=angel%20one");
    const brokerBaseUrl = (getBrokerApiBaseUrl() || "").replace(/\/$/, "");
    const authenticatedBaseUrl = (getAuthenticatedApiBaseUrl() || "").replace(/\/$/, "");
    const normalizedBaseUrl = baseUrl.replace(/\/$/, "");
    const candidateBaseUrls = (
      isLocalLikeHost
        ? [brokerBaseUrl, authenticatedBaseUrl, normalizedBaseUrl, localBaseUrl]
        : [brokerBaseUrl, authenticatedBaseUrl, normalizedBaseUrl]
    ).filter(Boolean).filter(
      (value, index, array) =>
        array.findIndex((item) => item.replace(/\/$/, "") === value.replace(/\/$/, "")) === index,
    );

    authDebug("broker-connect:candidates", {
      connectPath,
      candidates: candidateBaseUrls,
      authenticatedBackend: authenticatedBaseUrl || null,
      currentBaseUrl: normalizedBaseUrl,
      isAngelOneBrokerConnect,
    });

    let redirectUrl = null;
    let lastError = null;
    const attemptHistory = [];
    for (const candidateBaseUrl of candidateBaseUrls) {
      try {
        let candidateToken = getAuthToken() || initialAccessToken;
        let nextRedirectUrl;
        try {
          nextRedirectUrl = await requestConnect(candidateBaseUrl, candidateToken);
        } catch (candidateError) {
          if (candidateError.response?.status === 401 && storedRefreshToken) {
            candidateToken = await refreshForBackend(candidateBaseUrl);
            nextRedirectUrl = await requestConnect(candidateBaseUrl, candidateToken);
          } else {
            throw candidateError;
          }
        }
        if (!nextRedirectUrl) {
          continue;
        }
        if (nextRedirectUrl.includes("/broker_auth_login/")) {
          lastError = new Error("Broker login did not return the broker redirect URL. Please try again after refreshing the page.");
          continue;
        }
        if (isAngelOneBrokerConnect && isLegacyAngelOneRedirect(nextRedirectUrl)) {
          lastError = new Error("Legacy Angel One login URL detected. Please restart the frontend and use the local Django backend for broker login.");
          continue;
        }
        redirectUrl = nextRedirectUrl;
        persistBrokerBackend(candidateBaseUrl);
        persistAuthenticatedBackend(candidateBaseUrl);
        authDebug("broker-connect:success", {
          backend: candidateBaseUrl,
          connectPath,
          usedRetry: candidateToken !== initialAccessToken,
        });
        break;
      } catch (candidateError) {
        attemptHistory.push({
          backend: candidateBaseUrl,
          status: candidateError?.response?.status || null,
        });
        authDebug("broker-connect:failure", {
          backend: candidateBaseUrl,
          connectPath,
          status: candidateError?.response?.status || null,
        });
        lastError = candidateError;
        if (candidateError.response?.status === 500 || candidateError.response?.status === 404) {
          continue;
        }
      }
    }

    if (!redirectUrl) {
      const historyMessage = attemptHistory.length
        ? ` Tried backends: ${attemptHistory.map((attempt) => `${attempt.backend} (${attempt.status || "error"})`).join(", ")}.`
        : "";
      if (lastError) {
        lastError.message = `${extractErrorMessage(lastError)}${historyMessage}`;
      }
      throw lastError || new Error("Broker connect flow did not return a redirect URL.");
    }

    return { redirect_url: redirectUrl };
  } catch (error) {
    console.error('Error startBrokerConnectFlow:', error);
    if (error.message === "Network Error") {
      throw new Error(`Unable to reach the broker login endpoint at ${baseUrl}${connectPath}. Please make sure the Django backend is running and accessible.`);
    }
    throw new Error(extractErrorMessage(error));
  }
};

export const getCompanyDetails = async () => {
  let token = getAuthToken();

  if (!token) {
    console.error('No authentication token found.');
    return {};
  }

  try {
    const response = await axios.get(`${baseUrl}/get-company-profile/`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        try {
          token = await refreshToken();
          const retryResponse = await axios.get(`${baseUrl}/get-company-profile/`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          return retryResponse.data;
        } catch (refreshError) {
          console.error('Refresh token error:', refreshError);
          return {};
        }
      }
    }

    console.error('Error fetching getCompanyDetails:', error.response?.data?.detail || 'Failed to getCompanyDetails');
    return {};
  }
};

export const updateCompanyDetails = async (companyData) => {

  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.put(`${baseUrl}/update-company-profile/`, companyData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to update Company Details";
    if (error.response?.data?.code === "token_not_valid") {
      alert("Your session has expired. Please log in again.");
    }
    throw new Error(errorMessage);
  }
};

export const getSmtpDetails = async () => {

  let token = getAuthToken();

  if (!token) {
    handleNoTokenError();
    // throw new Error('No authentication token found.');
    return {};
  }

  try {
    const response = await axios.get(`${baseUrl}/get-company-smtp/`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    if (error.response?.data?.code === 'token_not_valid') {
      const messages = error.response?.data?.messages || [];
      const isAccessTokenInvalid = messages.some(
        (msg) => msg.token_class === 'AccessToken' && msg.message === 'Token is invalid or expired'
      );

      if (isAccessTokenInvalid) {
        try {
          token = await refreshToken();
          const retryResponse = await axios.get(`${baseUrl}/get-company-profile/`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          return retryResponse.data;
        } catch (refreshError) {
          console.error('Refresh token error:', refreshError);
          handleAuthError();
          // throw new Error('Session expired. Please log in again.');
          return {};
        }
      }
    }

    console.error('Error fetching getSmtpDetails:', error.response?.data?.detail || 'Failed to getSmtpDetails');
    // showAlert('error', 'Error', error.response?.data?.detail || 'Failed to getSmtpDetails. Please try again later.');
    // throw new Error(error.response?.data?.detail || 'Failed to fetch user profile');
    return {};
  }
};

export const updateSmtpDetails = async (data) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.put(`${baseUrl}/update-company-smtp/`, data, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to update SMTP Details";
    if (error.response?.data?.code === "token_not_valid") {
      alert("Your session has expired. Please log in again.");
    }
    throw new Error(errorMessage);
  }
};

export const testSmtpDetails = async (data = {}) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.post(`${baseUrl}/test-company-smtp/`, data, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.message || error.response?.data?.detail || "Failed to test SMTP Details";
    throw new Error(errorMessage);
  }
};

export const getWebsocket = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-websocket-token/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("getWebsocket:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching getWebsocket:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to fetch WebSocket details."
    );
  }
};

export const updateWebSocket = async (data) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.put(`${baseUrl}/update-websocket-token/`, data, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to update WebSocket token.";
    if (error.response?.data?.code === "token_not_valid") {
      alert("Your session has expired. Please log in again.");
    }
    throw new Error(errorMessage);
  }
};

export const handleAuthCallback = async (state, callbackPayload) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const params = new URLSearchParams({ state });
    if (callbackPayload?.code) params.set('code', callbackPayload.code);
    if (callbackPayload?.auth_token) params.set('auth_token', callbackPayload.auth_token);
    if (callbackPayload?.refresh_token) params.set('refresh_token', callbackPayload.refresh_token);
    if (callbackPayload?.feed_token) params.set('feed_token', callbackPayload.feed_token);

    const response = await axios.get(`${baseUrl}/auth-callback?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.data.access_token) {
      localStorage.setItem('apiAccessToken', response.data.access_token); // Store token in localStorage
      console.log('Token stored in localStorage:', localStorage.getItem('apiAccessToken'));
    } else {
      console.error('No access token in response');
    }

    return response.data;
  } catch (error) {
    console.error('Error with API call:', error.response?.data?.message || error.message);
    throw new Error(error.response?.data?.message || 'API call failed.');
  }
};

export const createRazorpayOrder = async (license_price, license_qty) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/create-order/`, { license_price, license_qty }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error creating Razorpay order:', error);
    throw new Error(error.response?.data?.message || 'Failed to create Razorpay order.');
  }
};

export const verifyRazorpayPayment = async (paymentData) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/verify-payment`, paymentData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error verifying Razorpay payment:', error);
    throw new Error(error.response?.data?.message || 'Failed to verify Razorpay payment.');
  }
};

export const getTradeStrategy = async () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-strategies-tradehistory/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("getTradeStrategy:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching getTradeStrategy:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to fetch getTradeStrategy."
    );
  }
};

export const getBrokerTokenExpiry = async () => {
  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/get-broker-token-expiry/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("getBrokerTokenExpiry:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching getBrokerTokenExpiry:", error);
    throw new Error(
      error.response?.data?.detail || "Failed to fetch getBrokerTokenExpiry."
    );
  }
};

export const SearchUsers = async (q) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/users-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        q: q,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const SearchActiveUsers = async (q) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/active-client-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        q: q,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const SearchInactiveUsers = async (q) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/inactive-client-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        q: q,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const SearchAllClients = async (q) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/get-client-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        q: q,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const SearchAllExpiryClients = async (q) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/expiry-clients-list/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        q: q,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const TradeHistorySearch = async (q, page_size) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/get-trade-history/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        page_size,
        q: q,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const TradeViewSearch = async (q, page_size) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/get-client-trade-history/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        q: q,
        page_size
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const TradeStatusSearch = async (q) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/get-client-Trade-status/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        q: q,
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const getTradeCounts = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/clients/trading/status/count/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('Fetched getTradeCounts:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching getTradeCounts:', error);
    throw new Error(error.response?.data?.message || "Failed to fetch getTradeCounts.");
  }
};

export const getOnboardClients = async (filter, fromDate, toDate) => {
  const token = getAuthToken()
  if (!token) {
    throw new Error("No authentication token found.")
  }

  try {
    const response = await axios.get(`${baseUrl}/clients/onboarding/stats/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        filter,
        from_date: fromDate,
        to_date: toDate
      },
    })
    console.log('Fetched getOnboardClients:', response.data)
    return response.data
  } catch (error) {
    console.error('Error fetching getOnboardClients:', error)
    throw new Error(error.response?.data?.message || "Failed to fetch getOnboardClients.")
  }
}

export const fetchClientLoginActivity = async (userId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/user-activity-log/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      params: {
        user_id: userId,
      },
    });
    console.log('Fetched getClientLoginActivity:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching getClientLoginActivity:', error);
    throw new Error(error.response?.data?.message || "Failed to fetch getClientLoginActivity.");
  }
};

export const getExecutionNodes = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/execution-nodes/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching execution nodes:', error);
    throw new Error(error.response?.data?.message || error.response?.data?.detail || "Failed to fetch execution nodes.");
  }
};

export const createExecutionNode = async (payload) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/execution-nodes/`, payload, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error creating execution node:', error);
    throw new Error(error.response?.data?.message || error.response?.data?.detail || "Failed to create execution node.");
  }
};

export const assignExecutionNodeToClient = async (clientId, nodeId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/execution-nodes/assign/`, {
      client_id: clientId,
      node_id: nodeId,
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error assigning execution node:', error);
    throw new Error(error.response?.data?.message || error.response?.data?.detail || "Failed to assign execution node.");
  }
};

export const releaseExecutionNodeFromClient = async (clientId) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.post(`${baseUrl}/execution-nodes/release/`, {
      client_id: clientId,
    }, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error releasing execution node:', error);
    throw new Error(error.response?.data?.message || error.response?.data?.detail || "Failed to release execution node.");
  }
};

export const getMyExecutionNode = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/client/execution-node/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching client execution node:', error);
    throw new Error(error.response?.data?.message || error.response?.data?.detail || "Failed to fetch execution IP.");
  }
};

export const saveMyExecutionNode = async (payload, hasExistingNode = false) => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const request = hasExistingNode ? axios.patch : axios.post;
    const response = await request(`${baseUrl}/client/execution-node/`, payload, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error saving client execution node:', error);
    throw new Error(error.response?.data?.message || error.response?.data?.detail || "Failed to save execution IP.");
  }
};

export const releaseMyExecutionNode = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.delete(`${baseUrl}/client/execution-node/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error releasing client execution node:', error);
    throw new Error(error.response?.data?.message || error.response?.data?.detail || "Failed to release execution IP.");
  }
};

export const getTradeResponse = async (id) => {
  console.log("Inside getTradeResponse with clientId:", id);

  const token = localStorage.getItem("authToken");
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/trade-order-response/${id}/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("Client response:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error fetching getTradeResponse by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch getTradeResponse by ID.");
  }
};

export const getClientBrokerTradeAlert = async () => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }

  try {
    const response = await axios.get(`${baseUrl}/client-broker-details-setting-aleart/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    console.log('Fetched getClientBrokerTradeAlert:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching getClientBrokerTradeAlert:', error);
    throw new Error(error.response?.data?.message || "Failed to fetch getClientBrokerTradeAlert.");
  }
};
