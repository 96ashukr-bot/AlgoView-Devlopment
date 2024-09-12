import axios from "axios";

const baseUrl = "http://127.0.0.1:8000";

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


// export const updateKYC = async (formData) => {
//   try {
//     const response = await axios.post(`${baseUrl}/api/kyc/`, formData, {
//       headers: {
//         "Content-Type": "multipart/form-data",
//       },
//     });
//     return response.data;
//   } catch (error) {
//     throw new Error(
//       error.response?.data?.message || "Failed to upload KYC document."
//     );
//   }
// };