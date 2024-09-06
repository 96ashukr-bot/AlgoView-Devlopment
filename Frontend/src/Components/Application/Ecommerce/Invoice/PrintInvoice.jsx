import { P } from '../../../../AbstractElements';
import paypal from '../../../../assets/images/other-images/paypal.png';
import React, { Fragment } from 'react';
import { Col, Form, Input, Row } from 'reactstrap';

const PrintInvoice = () => {
    return (
        <Fragment>
            <Row className="mt-3">
                <Col md="8">
                    <div>
                        <P attrPara={{ className: 'legal' }}><strong>Thank you for your business!</strong> Payment is expected within 31 days; please process this invoice within that time. There will be a 5% interest charge per month on late invoices.</P>
                    </div>
                </Col>
                <Col md="4">
                    <Form className="float-end invo-pal">
                        <Input type="image" src={paypal} name="submit" alt="PayPal - The safer, easier way to pay online!" />
                    </Form>
                </Col>
            </Row>
        </Fragment>
    );
};
export default PrintInvoice;