import axios from "axios";

const baseUrl = "http://127.0.0.1:8000";

const getAuthToken = () => {
  const token = localStorage.getItem('authToken');
  console.log('Retrieved token:', token); // Debugging line
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
  try {
    const formData = new FormData();
    
    formData.append('UserName', formValues.name);
    formData.append('Date_Of_Birth', formValues.dateOfBirth);
    formData.append('email', formValues.email || '');
    formData.append('phone', formValues.phoneNumber);
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
        "Content-Type": "multipart/form-data",
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
    throw new Error(error.response?.data?.message || "OTP verification failed");
  }
};

export const changePassword = async (oldPassword, newPassword, confirmNewPassword) => {
  try {
    const response = await axios.post(`${baseUrl}/change-password/`, {
      OldPassword: oldPassword,
      NewPassword: newPassword,
      ConfirmNewPassword: confirmNewPassword
    }, {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    const errorMessage = error.response?.data?.detail || "Failed to change password";
    throw new Error(errorMessage);
  }
};

