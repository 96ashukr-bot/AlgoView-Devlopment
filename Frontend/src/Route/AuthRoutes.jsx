import CreatePwd from '../Components/Pages/Auth/CreatePwd';
import ForgetPwd from '../Components/Pages/Auth/ForgetPwd';
import LoginOne from '../Components/Pages/Auth/LoginOne';
import LoginSweetalert from '../Components/Pages/Auth/LoginSweetalert';
import LoginTooltip from '../Components/Pages/Auth/LoginTooltip';
import LoginTwo from '../Components/Pages/Auth/LoginTwo';
import LoginValidation from '../Components/Pages/Auth/LoginValidation';
import Maintenance from '../Components/Pages/Auth/Maintenance';
import RegisterBgImg from '../Components/Pages/Auth/RegisterBgImg';
import RegisterSimple from '../Components/Pages/Auth/RegisterSimple';
import RegisterVideo from '../Components/Pages/Auth/RegisterVideo';
import UnlockUser from '../Components/Pages/Auth/UnlockUser';
import ErrorPage1 from '../Components/Pages/ErrorPages/ErrorPage400';
import ErrorPage2 from '../Components/Pages/ErrorPages/ErrorPage401';
import ErrorPage3 from '../Components/Pages/ErrorPages/ErrorPage403';
import ErrorPage4 from '../Components/Pages/ErrorPages/ErrorPage404';
import Logins from '../Auth/Signin';
import LoginForm from '../Components/Pages/Auth/LoginForm';
import Error500 from '../Components/Pages/ErrorPages/ErrorPage500';
import Error503 from '../Components/Pages/ErrorPages/ErrorPage503';
import PasswordResetPage from '../Components/Pages/Auth/PasswordResetPage';
import VerifyOTP from '../Components/Pages/Auth/VerifyOTP';
 
export const authRoutes = [
  { path: `/login`, Component: <Logins /> },
  { path: `/pages/authentication/login-simple/:layout`, Component: <LoginForm /> },
  { path: `/pages/authentication/verify-otp/:layout`, Component: <VerifyOTP />},
  { path: `/pages/authentication/login-img/:layout`, Component: <LoginOne /> },
  { path: `/pages/authentication/login-bg-img/:layout`, Component: <LoginTwo /> },
  { path: `/pages/authentication/login-validation/:layout`, Component: <LoginValidation /> },
  { path: `/pages/authentication/login-tooltip/:layout`, Component: <LoginTooltip /> },
  { path: `/pages/authentication/login-sweetalert/:layout`, Component: <LoginSweetalert /> },
  { path: `/pages/authentication/register-simple/:layout`, Component: <RegisterSimple /> },
  { path: `/pages/authentication/register-bg-img/:layout`, Component: <RegisterBgImg /> },
  { path: `/pages/authentication/register-video/:layout`, Component: <RegisterVideo /> },
  { path: `/pages/authentication/unlock-user/:layout`, Component: <UnlockUser /> },
  { path: `/pages/authentication/forget-pwd/:layout`, Component: <ForgetPwd /> },
  { path: `/pages/authentication/create-pwd/:layout`, Component: <CreatePwd /> },
  { path: `/pages/authentication/maintenance/:layout`, Component: <Maintenance /> },

  //Error
  { path: `/pages/errors/error400/:layout`, Component: <ErrorPage1 /> },
  { path: `/pages/errors/error401/:layout`, Component: <ErrorPage2 /> },
  { path: `/pages/errors/error403/:layout`, Component: <ErrorPage3 /> },
  { path: `/pages/errors/error404/:layout`, Component: <ErrorPage4 /> },
  { path: `/pages/errors/error500/:layout`, Component: <Error500 /> },
  { path: `/pages/errors/error503/:layout`, Component: <Error503 /> },

  // Password Reset
  { path: `/pages/authentication/reset-password/:uid/:token/:layout`, Component: <PasswordResetPage /> }, 

];
