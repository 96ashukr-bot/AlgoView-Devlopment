import { Film, Image, File } from 'react-feather';

export const errorPages = [

    { path: `/pages/errors/error400`, title: 'Error 400', type: 'link' },
    { path: `/pages/errors/error401`, title: 'Error 401', type: 'link' },
    { path: `/pages/errors/error403`, title: 'Error 403', type: 'link' },
    { path: `/pages/errors/error404`, title: 'Error 404', type: 'link' },
    { path: `/pages/errors/error500`, title: 'Error 500', type: 'link' },
    { path: `/pages/errors/error503`, title: 'Error 503', type: 'link' }
];
export const authPages = [
    { path: `/pages/authentication/login-simple/:layout`, type: 'link', title: 'Login Simple' },
    { path: `/pages/authentication/login-img`, type: 'link', title: 'Login with Bg Img 1' },
    { path: `/pages/authentication/login-bg-img`, type: 'link', title: 'Login with Bg Img 2' },
    { path: `/pages/authentication/login-validation`, type: 'link', title: 'Login With Validation' },
    { path: `/pages/authentication/register-simple/:layout`, type: 'link', title: 'Register Simple' },
    { path: `/pages/authentication/register-bg-img`, type: 'link', title: 'Register With Bg Image 1' },
    { path: `/pages/authentication/register-video`, type: 'link', title: 'Register With Video' },

];
export const usefullPages = [
    { path: `/pages/authentication/unlock-user`, type: 'link', title: 'Unlock User' },
    { path: `/pages/authentication/forget-pwd/:layout`, type: 'link', title: 'Forget Password' },
    { path: `/pages/authentication/create-pwd`, type: 'link', title: 'Create Password' },
    { path: `/pages/authentication/maintenance`, type: 'link', title: 'Maintenance' }
];

export const comingsoonPages = [
    { path: `/pages/comingsoon/comingsoon`, title: 'Coming-soon', icon: File, type: 'link' },
    { path: `/pages/comingsoon/comingsoonVideo`, title: 'Coming-video', icon: Film, type: 'link' },
    { path: `/pages/comingsoon/comingsoonImg`, title: 'Coming-image', icon: Image, type: 'link' },
];