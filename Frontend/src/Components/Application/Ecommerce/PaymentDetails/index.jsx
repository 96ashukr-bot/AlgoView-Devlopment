import React, { Fragment } from 'react';
import CashonDelivery from './Cod';
import CreditCards from './CreditCard';
import DebitCards from './DebitCard';
import EMIs from './Emi';
import NetBankings from './NetBanking';
import { Container, Row } from 'reactstrap';
import { Breadcrumbs } from '../../../../AbstractElements';

const PaymentDetailContain = () => {
    return (
        <Fragment>
            <Breadcrumbs parent="Ecommerce" title="Products Details" mainTitle="Products Details" />
            <Container fluid={true} className="credit-card">
                <Row>
                    <CreditCards />
                    <DebitCards />
                    <CashonDelivery />
                    <EMIs />
                    <NetBankings />
                </Row>
            </Container>
        </Fragment>
    );
};
export default PaymentDetailContain;