import React, { Fragment, useEffect, useMemo, useState } from 'react';
import { Col, Card, CardHeader, CardBody, Row } from 'reactstrap';
import { FaEye } from 'react-icons/fa';
import Swal from 'sweetalert2';
import 'sweetalert2/dist/sweetalert2.min.css';
import './ApiKeys.css';
import { getBroker } from '../../../../Services/Authentication';
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
import upStoxGuide from '../../../../assets/images/logo/upstoxlogin.png';
import zerodhaGuide from '../../../../assets/images/logo/zerodhalogin.png';

const brokerAssetMap = {
    upstox: { logo: upstocksLogo, guideImage: upStoxGuide },
    zerodha: { logo: zerodhaLogo, guideImage: zerodhaGuide },
    '5paisa': { logo: paisaLogo, guideImage: null },
    'alice blue': { logo: aliceblue, guideImage: null },
    dhan: { logo: dhanLogo, guideImage: null },
    'angel one': { logo: angelOneLogo, guideImage: null },
    'market hub': { logo: marketHubLogo, guideImage: null },
    'master trust': { logo: masterTrustLogo, guideImage: null },
    fyers: { logo: fyersLogo, guideImage: null },
    'kotak neo': { logo: kotakLogo, guideImage: null },
};

const brokerDocs = {
    upstox: {
        links: [
            { label: 'Upstox Developer Console', href: 'https://upstox.com/developer/' },
        ],
    },
    zerodha: {
        links: [
            { label: 'Zerodha Kite Connect', href: 'https://kite.trade/' },
        ],
    },
    '5paisa': {
        links: [
            { label: '5Paisa Developer Portal', href: 'https://www.5paisa.com/developer-api' },
        ],
    },
    'alice blue': {
        links: [
            { label: 'Alice Blue ANT', href: 'https://ant.aliceblueonline.com/' },
        ],
    },
    dhan: {
        links: [
            { label: 'Dhan Developer Portal', href: 'https://dhanhq.co/' },
        ],
    },
    'angel one': {
        links: [
            { label: 'Angel One SmartAPI', href: 'https://smartapi.angelone.in/' },
        ],
    },
    fyers: {
        links: [
            { label: 'FYERS API Dashboard', href: 'https://myapi.fyers.in/dashboard' },
        ],
    },
    'kotak neo': {
        links: [
            { label: 'Kotak Neo TradeAPI Portal', href: 'https://napi.kotaksecurities.com/devportal/apis' },
        ],
    },
};

const formatAuthMode = (authMode) => (authMode || 'broker_specific').replace(/_/g, ' ');

const renderFieldChecklist = (fields) => {
    if (!fields?.length) {
        return '<p>No broker-specific credentials are required from the panel for this broker.</p>';
    }

    const items = fields
        .map(
            (field) =>
                `<li><strong>${field.label}</strong>${field.required ? ' (required)' : ''}${field.secret ? ' - stored securely' : ''}</li>`
        )
        .join('');

    return `
        <p><strong>Broker setup fields:</strong></p>
        <ul style="padding-left: 20px; margin-bottom: 12px;">${items}</ul>
    `;
};

const buildInstructionHtml = (broker) => {
    const normalizedName = broker.broker_name.toLowerCase();
    const schema = broker.setup_schema || {};
    const connectLabel = schema.connect_action_label || 'Broker Login';
    const fieldChecklist = renderFieldChecklist(schema.fields);
    const docs = brokerDocs[normalizedName]?.links || [];
    const guideImage = brokerAssetMap[normalizedName]?.guideImage;

    const connectStep = schema.connect_path
        ? `<p><strong>Step 3:</strong> Use the dashboard action <strong>${connectLabel}</strong> to start the broker-side authentication flow.</p>`
        : `<p><strong>Step 3:</strong> Complete the broker authentication flow outside AlgoView if this broker does not support a panel login button.</p>`;

    const docsHtml = docs.length
        ? `<p><strong>Reference links:</strong></p><ul style="padding-left: 20px;">${docs
              .map((doc) => `<li><a href="${doc.href}" target="_blank" rel="noreferrer">${doc.label}</a></li>`)
              .join('')}</ul>`
        : '';

    const imageHtml = guideImage
        ? `<img src="${guideImage}" alt="${broker.broker_name} guide" style="max-width: 220px; margin: 8px 0; width: 100%;" />`
        : '';

    const authModeHtml = `<p><strong>Authentication mode:</strong> ${formatAuthMode(schema.auth_mode)}</p>`;
    const callbackHtml = schema.supports_callback
        ? '<p><strong>Callback:</strong> AlgoView expects the broker to redirect back to the configured callback URL after successful authentication.</p>'
        : '';

    return `
        <h4>${broker.broker_name} Setup</h4>
        <p>Kindly follow these steps to link your account with this Algo Software.</p>
        <div style="text-align: left;">
            <p><strong>Step 1:</strong> Open the Client Dashboard and use <strong>Select Broker</strong> to choose <strong>${broker.broker_name}</strong>.</p>
            <p><strong>Step 2:</strong> Save only the broker-specific fields shown in the broker setup screen.</p>
            ${fieldChecklist}
            ${authModeHtml}
            ${connectStep}
            ${callbackHtml}
            ${imageHtml}
            ${docsHtml}
        </div>
    `;
};

const ApiKeys = () => {
    const [brokers, setBrokers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadBrokers = async () => {
            try {
                const response = await getBroker();
                setBrokers(Array.isArray(response) ? response : []);
            } catch (error) {
                setBrokers([]);
            } finally {
                setLoading(false);
            }
        };

        loadBrokers();
    }, []);

    const brokerCards = useMemo(
        () =>
            brokers.map((broker) => {
                const normalizedName = broker.broker_name.toLowerCase();
                return {
                    ...broker,
                    logo: brokerAssetMap[normalizedName]?.logo || marketHubLogo,
                    instructions: buildInstructionHtml(broker),
                };
            }),
        [brokers]
    );

    const handleIconClick = (broker) => {
        Swal.fire({
            title: `${broker.broker_name} API Information`,
            html: broker.instructions,
            icon: 'info',
            confirmButtonText: 'Close',
            customClass: { popup: 'swal2-dark' },
            className: 'custom-swal-style',
        });
    };

    return (
        <Fragment>
            <Col sm="12">
                <Card className="main-card">
                    <CardHeader className="text-center">
                        <h3>Broker Setup Help</h3>
                        <p>Broker onboarding steps now follow the same broker-specific schema used in the client setup flow.</p>
                    </CardHeader>
                    <CardBody>
                        {loading ? (
                            <p className="text-center mb-0">Loading broker setup help...</p>
                        ) : (
                            <Row className="justify-content-center">
                                {brokerCards.map((broker, index) => (
                                    <Col key={broker.id || index} sm="6" md="4" lg="3" className="mb-4">
                                        <Card className="broker-card">
                                            <div className="card-content">
                                                <img
                                                    src={broker.logo}
                                                    alt={`${broker.broker_name} Logo`}
                                                    className="broker-logo"
                                                />
                                                <p className="broker-name">{broker.broker_name}</p>
                                                <small style={{ color: '#6b7280', textTransform: 'capitalize' }}>
                                                    {formatAuthMode(broker.setup_schema?.auth_mode)}
                                                </small>
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
                        )}
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default ApiKeys;
