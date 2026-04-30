import React, { useEffect } from 'react';
import Swal from 'sweetalert2';
import {
  getClientBrokerTradeAlert,
  getBrokerRuntimeStatus,
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
            <p style="margin-bottom: 15px;"><strong>Step 2: Broker Setup</strong>: Fill only the broker-specific fields shown after selection and save them.</p>
            <p style="margin-bottom: 15px;"><strong>Step 3: Broker Login / Connect</strong>: Complete the daily login or redirect-based connect flow required by that broker before trading starts.</p>
            <p style="margin-bottom: 15px;"><strong>Manually Broker Logged In</strong>: For brokers like <strong> Alice Blue , Dhan </strong>.  Log in daily on their specific dashboards.</p>
            <p style="margin-bottom: 15px;"><strong>ANGLE ONE</strong>: Save API key, client ID, password, and TOTP secret in the broker setup screen. AlgoView stores them securely for future session recovery.</p>
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

          const fieldsMatch = response.message.match(/: ([\w\s,]+)/);
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
          getBrokerRuntimeStatus()
            .then((runtime) => {
              const sessionStatus = runtime?.session?.status || 'unavailable';
              const tokenStatus = runtime?.token?.status || 'unavailable';
              const isActive = Boolean(
                runtime?.session?.is_active ||
                runtime?.token?.is_active ||
                sessionStatus === 'active' ||
                tokenStatus === 'active'
              );

              if (!isActive) {
                const message =
                  tokenStatus === 'expired'
                    ? 'Broker token has expired. Please log in again to continue trading.'
                    : 'Please log in again to continue trading. You are not logged in yet.';

                Swal.fire({
                  title: 'Broker Login Session',
                  text: message,
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
              console.error('Error fetching broker runtime status:', error);
            });
        }
      });
  }, []);

  return <div></div>;
};

export default ClientAlert;
