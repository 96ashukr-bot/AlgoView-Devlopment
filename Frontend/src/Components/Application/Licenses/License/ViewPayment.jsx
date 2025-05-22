import React, { Fragment, useContext } from 'react';
import { H4, LI, UL, } from '../../../../AbstractElements';
import HeaderCard from '../../../Common/Component/HeaderCard';
import './License.css';
import CartContext from '../../../../_helper/Ecommerce/Cart';
import { Col, Input, Label, Row, Card, Container, Button, CardBody } from 'reactstrap';

const ViewPayment = () => {
    const { cart } = useContext(CartContext);
    return (
        <Fragment>
            <div>
                {/* <Breadcrumbs parent='Ecommerce' title='Checkout' mainTitle='Checkout' /> */}
                <Container fluid={true} className="d-flex justify-content-center align-items-center vh-100">
                    <Row className="justify-content-center w-100">
                        <Col xl="8" lg="10" md="10" sm="12">
                            <Card className="checkout">
                                <div className="text-center">
                                    <HeaderCard title='License Payment Details' />
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
                                                    cart.map((item) => {
                                                        return (
                                                            <UL attrUL={{ className: 'simple-list border-x-0 border-t-0 qty' }} key={item.id}>
                                                                <LI attrLI={{ className: 'border-0' }}>
                                                                    {item.name} x {item.qty}
                                                                    <span>${item.price}</span>
                                                                </LI>
                                                            </UL>
                                                        );
                                                    })}
                                                <UL attrUL={{ className: 'simple-list border-0  sub-total' }}>
                                                    <LI attrLI={{ className: 'border-0 bg-transparent' }}>
                                                        No. Of License <span className="count">
                                                            <Input type="number" min="0" />
                                                        </span>
                                                    </LI>
                                                    <LI attrLI={{ className: 'shipping-class border-0  bg-transparent' }}>
                                                        License Price
                                                        <div className="shopping-checkout-option">
                                                            <Label className="d-block" htmlFor="chk-ani1">
                                                                <Input type="number" min="0" />
                                                            </Label>
                                                        </div>
                                                    </LI>
                                                </UL>
                                                <UL attrUL={{ className: 'simple-list sub-total total border-top pt-3 mt-3' }}>
                                                    <LI attrLI={{ className: 'border-0 bg-transparent ' }}>
                                                        Total <span className="count">0.00</span>
                                                    </LI>
                                                </UL>
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
export default ViewPayment;
