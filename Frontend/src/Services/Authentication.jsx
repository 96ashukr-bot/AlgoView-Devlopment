import axios from "axios";

const baseUrl = "http://127.0.0.1:8000";

const getAuthToken = () => {
  const token = localStorage.getItem('authToken');
  console.log('Retrieved token:', token);
  return token;
};


const login = async (email, password) => {
  try {
    const response = await axios.post(`${baseUrl}/login/`, {
      email: email,
      password: password,
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || "Login failed");
  }
};

export { login };

export const signupUser = async (formValues) => {
  try {
    const response = await axios.post(`${baseUrl}/signup/`, formValues, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    return response;
  } catch (error) {
    throw error;
  }
};

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

    formData.append('document_type', formValues.idType.toLowerCase().replace(/\s+/g, '_'));

    if (formValues.idFront instanceof File) {
      formData.append('document_file_front', formValues.idFront);
    }

    if (formValues.idBack instanceof File) {
      formData.append('document_file_back', formValues.idBack);
    }

    formData.append('is_verified', false);

    const response = await axios.post(`${baseUrl}/kyc/`, formData, {
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

export const verifyOtp = async (email, otp) => {
  try {
    const response = await axios.post(`${baseUrl}/verify-otp/`, {
      email: email,
      otp_code: otp
    });

    if (response.data.access) {
      localStorage.setItem('authToken', response.data.access);
      localStorage.setItem('refreshToken', response.data.refresh);

      console.log('Access Token stored:', response.data.access);
      console.log('Refresh Token stored:', response.data.refresh);
    }

    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || "OTP is expired! Please resend the OTP.");
  }
};

export const resendOtp = async (email) => {
  try {
    const response = await axios.post(`${baseUrl}/resend-otp/`, {
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
  const token = getAuthToken();
  if (!token) {
    throw new Error("No authentication token found.");
  }
  try {
    const response = await axios.get(`${baseUrl}/user-profile/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching user profile:", error);
    if (error.response?.data?.code === "token_not_valid") {
      // Handle token refresh or logout
      alert("Your session has expired. Please log in again.");
      // Optionally redirect to login page
    }
    throw new Error(error.response?.data?.detail || "Failed to fetch user profile");
  }
};

export const updateUserProfile = async (formValues) => {
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

export const fetchUserData = async (formValues) => {
  try {
    const response = await axios.get(`${baseUrl}/users/`, formValues, {});
    return response.data;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
};

export const fetchRolesList = async (formValues) => {
  try {
    const response = await axios.get(`${baseUrl}/get-roles-list/`, formValues, {});
    return response.data;
  } catch (error) {
    console.error('Error fetching roles:', error);
    throw error;
  }
};

export const fetchRolePermissions = async (formValues) => {
  try {
    const response = await axios.get(`${baseUrl}/role-permissions/`, formValues, {});
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
  const response = await fetch('http://127.0.0.1:8000/create-roles/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify(roleData),
  });

  if (!response.ok) {
      throw new Error('Failed to create role');
  }
  
  const data = await response.json();
  return data;
};

export const deleteRole = async (roleId) => {
  const response = await axios.delete(`${baseUrl}/delete-roles/${roleId}`);

  if (response.status !== 200) {
      throw new Error('Failed to delete the role');
  }

  return response.data; 
};
