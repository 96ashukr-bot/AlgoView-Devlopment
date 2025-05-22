import React, { Fragment, useContext, useState, useEffect } from 'react';
import { H4, LI, UL } from '../../../../AbstractElements';
import HeaderCard from '../../../Common/Component/HeaderCard';
import { BillingDetails } from '../../../../Constant';
import './License.css';
import { createRazorpayOrder, verifyRazorpayPayment } from '../../../../Services/Authentication';
import CartContext from '../../../../_helper/Ecommerce/Cart';
import { Col, Input, Label, Row, Card, Container, Button, CardBody } from 'reactstrap';

const Payment = () => {
    const { cart } = useContext(CartContext);
    const [license_qty, setLicenseQty] = useState(0);
    const [license_price, setLicensePrice] = useState(0);
    const [razorpayOrderId, setRazorpayOrderId] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const totalAmount = license_qty * license_price;

    useEffect(() => {
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.async = true;
        document.body.appendChild(script);

        return () => {
            document.body.removeChild(script);
        };
    }, []);

    const handleCreateOrder = async () => {
        try {
            const data = await createRazorpayOrder(license_price, license_qty);
            if (data.razorpay_order_id) {
                setRazorpayOrderId(data.razorpay_order_id);
                return true;
            } else {
                alert("Failed to create Razorpay order.");
                return false;
            }
        } catch (error) {
            console.error(error.message);
            alert("An error occurred while creating the Razorpay order.");
            return false;
        }
    };

    const handlePayment = () => {
        if (!razorpayOrderId) {
            alert("Razorpay order not created. Try again later.");
            return;
        }

        const options = {
            key: "",
            amount: totalAmount * 100,
            currency: "INR",
            order_id: razorpayOrderId,
            name: "AlgoSparks",
            description: "Test Transaction",
            handler: async (response) => {
                console.log(response);
                alert("Payment Successful!");

                try {
                    const data = await verifyRazorpayPayment({
                        ...response,
                        totalAmount,
                        license_price,
                        license_qty,
                    });
                    if (data.status === 'success') {
                        alert('Payment successfully verified');
                    } else {
                        alert('Payment verification failed');
                    }
                } catch (error) {
                    alert(error.message);
                }
            },
            prefill: {
                name: "John Doe",
                email: "john.doe@example.com",
                contact: "0000000000",
            },
            notes: {
                totalAmount: totalAmount.toFixed(2),
                license_price: license_price.toFixed(2),
                license_qty: license_qty,
            },
            theme: {
                color: "#F37254",
            },
        };

        const razorpayInstance = new window.Razorpay(options);
        razorpayInstance.open();
    };

    return (
        <Fragment>
            <div>
                <Container fluid className="d-flex justify-content-center align-items-center vh-100">
                    <Row className="justify-content-center w-100">
                        <Col xl="8" lg="10" md="10" sm="12">
                            <Card className="checkout">
                                <div className="text-center">
                                    <HeaderCard title={BillingDetails} />
                                </div>
                                <CardBody>
                                    <Row>
                                        <div className="checkout-details">
                                            <div className="order-box">
                                                <div className="title-box">
                                                    <div className="checkbox-title">
                                                        <H4>License </H4>
                                                        <span>Total</span>
                                                    </div>
                                                </div>
                                                {cart &&
                                                    cart.map((item) => (
                                                        <UL attrUL={{ className: 'simple-list border-x-0 border-t-0 qty' }} key={item.id}>
                                                            <LI attrLI={{ className: 'border-0' }}>
                                                                {item.name} x {item.qty}
                                                                <span>${item.price}</span>
                                                            </LI>
                                                        </UL>
                                                    ))}
                                                <UL attrUL={{ className: 'simple-list border-0 sub-total' }}>
                                                    <LI attrLI={{ className: 'border-0 bg-transparent' }}>
                                                        No. Of License
                                                        <span className="count">
                                                            <Input
                                                                type="number"
                                                                min="0"
                                                                value={license_qty}
                                                                onChange={(e) => setLicenseQty(Number(e.target.value))}
                                                            />
                                                        </span>
                                                    </LI>
                                                    <LI attrLI={{ className: 'shipping-class border-0 bg-transparent' }}>
                                                        License Price
                                                        <div className="shopping-checkout-option">
                                                            <Label className="d-block" htmlFor="chk-ani1">
                                                                <Input
                                                                    type="number"
                                                                    min="0"
                                                                    value={license_price}
                                                                    onChange={(e) => setLicensePrice(Number(e.target.value))}
                                                                />
                                                            </Label>
                                                        </div>
                                                    </LI>
                                                </UL>
                                                <UL attrUL={{ className: 'simple-list sub-total total border-top pt-3 mt-3' }}>
                                                    <LI attrLI={{ className: 'border-0 bg-transparent ' }}>
                                                        Total <span className="count">{totalAmount.toFixed(2)}</span>
                                                    </LI>
                                                </UL>
                                                <div className="border-top pt-3 text-center">
                                                    <Button
                                                        onClick={async () => {
                                                            setIsLoading(true);
                                                            const orderCreated = await handleCreateOrder();
                                                            if (orderCreated) {
                                                                handlePayment();
                                                            }
                                                            setIsLoading(false);
                                                        }}
                                                        color="success"
                                                        outline
                                                        className="px-4 py-2 custom-paynow-btn"
                                                        disabled={isLoading}
                                                    >
                                                        {isLoading ? 'Processing...' : 'Pay Now'}
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    </Row>
                                </CardBody>
                            </Card>
                        </Col>
                    </Row>
                </Container>
            </div>
        </Fragment>
    );
};

export default Payment;
