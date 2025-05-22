import React, { Fragment } from 'react';
import { Col, Card, CardHeader, CardBody, Row } from 'reactstrap';
import { FaEye } from 'react-icons/fa';
import Swal from 'sweetalert2';
import 'sweetalert2/dist/sweetalert2.min.css';
import './ApiKeys.css';
import aliceblue from '../../../../assets/images/logo/aliceblue.jpeg';
import zerodhaLogo from '../../../../assets/images/logo/zerodha.png';
import paisaLogo from '../../../../assets/images/logo/5paisa.png';
import angelOneLogo from '../../../../assets/images/logo/angelone.png';
import marketHubLogo from '../../../../assets/images/logo/markethub.png';
import masterTrustLogo from '../../../../assets/images/logo/mastertrust.png';
import fyersLogo from '../../../../assets/images/logo/fyers.png';
import kotakLogo from '../../../../assets/images/logo/kotakneo.png';
import upstocksLogo from '../../../../assets/images/logo/upstox.png';
import dhanLogo from '../../../../assets/images/logo/dhan.jpg';
import upStox from '../../../../assets/images/logo/upstoxlogin.png';
import panchPaisa from '../../../../assets/images/logo/panchpaisa.png';
import zerodha from '../../../../assets/images/logo/zerodhalogin.png';

const ApiKeys = () => {
    const brokers = [
        {
            name: "UPSTOX",
            details: "API Process of UPSTOX :",
            instructions: `
            <p><strong>Step 1:</strong> Client Dashboard --> First select the Broker UPSTOX ( Click on the 'Select Broker' Switch Toggle ).</p>
            <p><strong>Step 2:</strong> Client Dashboard --> Click on the 'Broker Login' Switch Toggle.</p>
            <p><strong>Step 3:</strong> After logging in as a broker, you will be redirected to the UPSTOX website, where you need to first enter your mobile number, followed by the OTP, and then the MPIN.</p>
            <img src="${upStox}" alt="UPSTOCKS Logo" style="max-width: 200px; margin-top: 5px; margin-bottom: 5px; width:100%" />
            <p>Step 4: After login, enter the following redirect URL :
            <a href="https://www.sparks.algoview.in/callback?code=Auth_code&state=upstox" target="_blank">https://www.sparks.algoview/callback?code=Auth_code&state=upstox</a></p>`,
            logo: upstocksLogo
        },
        {
            name: "ZERODHA",
            details: "API Process of Zerodha :",
            instructions: `
                           <p><strong>Step 1:</strong> Client Dashboard --> First select the Broker ZERODHA ( Click on the 'Select Broker' Switch Toggle ).</p>
                           <p><strong>Step 2:</strong> Client Dashboard --> Click on the 'Broker Login' Switch Toggle.</p>
                           <p>Step 4: <a href="https://kite.trade/" target="_blank">Click here</a> to log in to Zerodha Kite.</p>
                           <p><strong>Step 5:</strong> After logging in as a broker, you will be redirected to the UPSTOX website, where you need to first enter your mobile number, followed by the OTP, and then the PIN.</p>
                            <img src="${zerodha}" alt="UPSTOCKS Logo" style="max-width: 200px; margin-top: 5px; margin-bottom: 5px; width:100%" />
                           <p>Step 6: After login : 
                           <a href="https://www.sparks.algoview/backend/zerodha?key=YOUR_PANEL_CLIENT_KEY" target="_blank">https://www.sparks.algoview/backend/zerodha?key=YOUR_PANEL_CLIENT_KEY</a></p>`,
            logo: zerodhaLogo
        },
        {
            name: "5 PAISA",
            details: "API setup instructions for 5 Paisa :",
            instructions: `
                        <p><strong>Step 1:</strong> Client Dashboard --> First select the Broker 5Paisa ( Click on the 'Select Broker' Switch Toggle ).</p>
                        <p><strong>Step 2:</strong> Client Dashboard --> Click on the 'Broker Login' Switch Toggle.</p>
                        <p><strong>Step 3:</strong> After logging in as a broker, you will be redirected to the 5Paisa website, where you need to first enter your mobile number, followed by the OTP, and then the PIN.</p>
                        <img src="${panchPaisa}" alt="paisa Logo" style="max-width: 200px; margin-top: 5px; margin-bottom: 5px; width:100%" />
                        <p>Step 4: After login, enter the following redirect URL :
                        <a href="https://www.sparks.algoview.in/callback?code=Auth_code&state=5paisa" target="_blank">https://www.sparks.algoview/callback?code=Auth_code&state=5paisa</a></p>`,
            logo: paisaLogo
        },
        {
            name: "ALICE BLUE",
            details: "API Process of Alice Blue :",
            instructions: `
            <p><strong>Step 1:</strong> Login to the Aliceblue ANT web application: 
                           <a href="https://ant.aliceblueonline.com/" target="_blank">https://ant.aliceblueonline.com/</a></p>
                           <p><strong>Step 2:</strong> Navigate to APPS --> 'API key' Users can generate API key via the below button.</p>
                           <p><strong>Step 3:</strong> After accepting the 'Terms and Conditions', the generated API key will be sent to the User's registered mail.</p>
                           <p><strong>Step 4:</strong> For authentication and authorization work flow, use that 'API key'.</p>
                           <p><strong>Step 5:</strong> To use the ALICE BLUE API you need USERID AND APIKEY.</p>
                            <a href="https://www.sparks.algoview/callback?code=Auth_code&state=aliceblue" target="_blank">https://www.sparks.algoview/callback?code=Auth_code&state=aliceblue</a></p>
                           `,
            logo: aliceblue
        },
        {
            name: "DHAN",
            details: "Log in to your Dhan account :",
            instructions: `<p>Step 1: After login, enter the following redirect URL :</p>`,
            logo: dhanLogo
        },
        {
            name: "ANGEL ONE",
            details: "API Process of Angel One :",
            instructions: `<p><strong>Step 1:</strong> Sign up for Smart API: 
                           <a href="https://smartapi.angelbroking.com/signup" target="_blank">https://smartapi.angelbroking.com/signup</a></p>
                           <p><strong>Step 2:</strong> Login to Angel One Smart API: 
                           <a href="https://smartapi.angelbroking.com/signin#" target="_blank">https://smartapi.angelbroking.com/signin#</a></p>

                           <p><strong>Step 3:</strong> Create an App Choose the Trading API.</p>

                           <p><strong>Step 4:</strong> You will get the API KEY.</p>
                           <p><strong>Step 5:</strong> Enable TOTP using Angle One CLIENT ID and PIN: 
                           <a href="https://www.sparks.algoviewsmartapi.angelbroking.com/enable-totp" target="_blank">https://smartapi.angelbroking.com/enable-totp</a></p>
                           <p><strong>Step 6:</strong> To use ANGEL ONE API : ApiKey, ClientID, PIN, TOTP is Mandatory.</p>`,
            logo: angelOneLogo
        },
        {
            name: "MARKET HUB",
            details: "Log in to your Market Hub account :",
            instructions: `<p>Step 1: After login, enter the following redirect URL :</p>`,
            logo: marketHubLogo
        },
        {
            name: "MASTER TRUST",
            details: "Log in to your Master Trust account :",
            instructions: `<p>Step 1: After login, enter the following redirect URL :</p>`,
            logo: masterTrustLogo
        },
        {
            name: "FYERS",
            details: "API Process of Fyers :",
            instructions: `
                           <p><strong>Step 1:</strong> Sign in to the fyers API Web Portal using 4 digit PIN: 
                           <a href="https://login.fyers.in/?cb=https://myapi.fyers.in" target="_blank">https://login.fyers.in/?cb=https://myapi.fyers.in</a></p>
                           <p><strong>Step 2:</strong> Click on Create APP and Added the following details : -> App Name, Redirect URL & Description</p>
                           <p><strong>Step 3:</strong> App Permissions - Select Order Placement and  Historical Data.</p>
                           <p><strong>Step 4:</strong> After Creating API you will see your API which is inactive at: 
                           <a href="https://myapi.fyers.in/dashboard" target="_blank">https://myapi.fyers.in/dashboard</a></p>
                           <p><strong>Step 5:</strong> After successful login, user is redirected to the redirect uri with the auth_code where you need to  accept the terms and condition to active the url for the first time.</p>
                           <p><strong>Step 6:</strong> POST the auth_code and appIdHash (SHA-256 of api_id + app_secret) to Validate Authcode API endpoint.</p>
                           <p><strong>Step 7:</strong> Obtain the access_token use that for all the subsequent requests.</p>
                           <p><strong>Step 8:</strong> To use the FYERS API you need : -> 
                           redirect_uri, client_id, secret_key, grant_type, response_type, state & auth_code
                           </p>
                           `,
            logo: fyersLogo
        },
        {
            name: "KOTAK NEO",
            details: "API Process of Kotak Neo :",
            instructions: `<p><strong>Step 1:</strong> Visit our Neo TradeAPI Portal (Username and Password are the API Credentials that you receive after registering for Kotak Neo TradeAPI and note your Demat account credentials): 
                           <a href="https://napi.kotaksecurities.com/devportal/apis" target="_blank">https://napi.kotaksecurities.com/devportal/apis</a></p>
                           <p><strong>Step 2:</strong> Login and open application marked ‘Default application’.</p>

                           <p><strong>Step 3:</strong>On the left panel under ‘Production Keys’, click ‘OAuth2 Tokens’.</p>

                           <p><strong>Step 4:</strong>You will find your consumer key, access token, and your API secret.</p>
                           <p><strong>Step 5:</strong> Click ‘Generate access token’ and change the default validity of 3600 seconds to a validity period of your choice. (after this period elapses you will need to generate it again)</p>
                           <p><strong>Step 6:</strong> Once you have your consumer key and access token at your disposal, you can use the APIs.</p>`,
            logo: kotakLogo
        },

    ];

    const handleIconClick = (broker) => {
        Swal.fire({
            title: `${broker.name} API Information`,
            html: `<h4>${broker.details}</h4>
                   <p>Kindly follow these steps to link your account with this Algo Software.</p>
                   <div style="text-align: left;">${broker.instructions}</div>`,
            icon: 'info',
            confirmButtonText: 'Close',
            customClass: { popup: 'swal2-dark' },
            // width: '40%',
            className: 'custom-swal-style'
        });
    };

    return (
        <Fragment>
            <Col sm="12">
                <Card className="main-card">
                    <CardHeader className="text-center">
                        <h3>API Keys</h3>
                        <p>Manage your API keys and related settings.</p>
                    </CardHeader>
                    <CardBody>
                        <Row className="justify-content-center">
                            {brokers.map((broker, index) => (
                                <Col key={index} sm="6" md="4" lg="3" className="mb-4">
                                    <Card className="broker-card">
                                        <div className="card-content">
                                            <img
                                                src={broker.logo}
                                                alt={`${broker.name} Logo`}
                                                className="broker-logo"
                                            />
                                            <p className="broker-name">{broker.name}</p>
                                        </div>
                                        <div className="card-footer search-btn-clr">
                                            <FaEye
                                                className="eye-icon"
                                                onClick={() => handleIconClick(broker)}
                                            />
                                        </div>
                                    </Card>
                                </Col>
                            ))}
                        </Row>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default ApiKeys;
