import React, { useEffect } from 'react';
import Swal from 'sweetalert2';
import {
  getClientBrokerTradeAlert,
  getBrokerTokenExpiry,
  getClientBrokerDetail,
} from '../../../../Services/Authentication';

const ClientAlert = () => {
  useEffect(() => {
    const hasShownInitialAlert = localStorage.getItem('hasShownInitialAlert');
    // Initial mandatory steps alert
    if (!hasShownInitialAlert) {
      // Show Initial mandatory steps alert
      Swal.fire({
        title: 'Mandatory steps to start Trading with Algo.',
        html: `
          <div style="text-align: left;">
            <p style="margin-bottom: 15px;"><strong>Step 1: Select Broker</strong>: First, select the broker ( Select Broker ) to start trading.</p>
            <p style="margin-bottom: 15px;"><strong>Step 2: Broker Details</strong>: Fill in the proper broker details.</p>
            <p style="margin-bottom: 15px;"><strong>Step 3: Broker Login</strong>: Log in daily via click on the ( Broker Login ) toggle, before trading starts for brokers like <strong> Upstox, Zerodha, Fyers, and 5Paisa </strong></p>
            <p style="margin-bottom: 15px;"><strong>Manually Broker Logged In</strong>: For brokers like <strong> Alice Blue , Dhan </strong>.  Log in daily on their specific dashboards.</p>
            <p style="margin-bottom: 15px;"><strong>ANGLE ONE</strong>: If you are selected the  <strong> Angle One </strong> broker, then make sure your <strong> TOTP  </strong> Secret should be right , because in the case of ANGLE ONE broker activation is depend on the <strong> TOTP </strong> Secret. </p>
          </div>
        `,
        icon: 'info',
        confirmButtonText: 'Got It!',
        width: '40em',
        customClass: {
          popup: 'swal-popup',
        },
      }).then(() => {
        // Set flag in localStorage to prevent showing the alert again in this session
        localStorage.setItem('hasShownInitialAlert', 'true');
      });
    }

    let showTokenExpiryCheck = true;

    // Step 1: Check for missing broker fields
    getClientBrokerTradeAlert()
      .then((response) => {
        if (
          response.status === false &&
          response.message.includes('Missing fields for broker')
        ) {
          showTokenExpiryCheck = false;

          const brokerMatch = response.message.match(/broker '(\w+)'/);
          const fieldsMatch = response.message.match(/: ([\w\s,]+)/);
          const broker = brokerMatch ? brokerMatch[1] : 'Unknown Broker';
          const missingFields = fieldsMatch
            ? fieldsMatch[1].split(', ').map((field) => field.trim())
            : [];

          Swal.fire({
            title: 'Incomplete Broker Setup',
            html: `
              <div style="text-align: left;">
                <p>Missing required fields. Please complete the setup to start trading.</p>
                <p><strong>Missing Fields:</strong></p>
                <ul style="list-style-type: disc; padding-left: 20px;">
                  ${missingFields.map((field) => `<li>${field}</li>`).join('')}
                </ul>
              </div>
            `,
            icon: 'warning',
            confirmButtonText: 'Okay, I’ll Fix It!',
            width: '40em',
            customClass: {
              popup: 'swal-popup',
            },
          });
        }
      })
      .catch((error) => {
        console.error('Error checking broker fields:', error);
      })
      .finally(() => {
        if (showTokenExpiryCheck) {
          // Step 2: Get broker name to check if token expiry alert should be shown
          getClientBrokerDetail()
            .then((brokerRes) => {
              const brokerName =
                brokerRes?.data?.broker_name?.broker_name?.toUpperCase();
              const allowedBrokers = ['ZERODHA', 'UPSTOX', 'FYERS', '5PAISA'];

              if (allowedBrokers.includes(brokerName)) {
                // Step 3: Check if token is expired
                getBrokerTokenExpiry()
                  .then((res) => {
                    if (res?.isTokenExpired) {
                      Swal.fire({
                        title: 'Broker Login Session',
                        text:
                          res.message ||
                          'Please log in again to continue trading.',
                        icon: 'warning',
                        confirmButtonText: 'OK',
                        width: '30em',
                        customClass: {
                          popup: 'swal-popup',
                        },
                      });
                    }
                  })
                  .catch((error) => {
                    console.error('Error checking broker token expiry:', error);
                  });
              }
            })
            .catch((error) => {
              console.error('Error fetching broker detail:', error);
            });
        }
      });
  }, []);

  return <div></div>;
};

export default ClientAlert;
