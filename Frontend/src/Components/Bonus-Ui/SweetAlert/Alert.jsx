import React, { Fragment, useState } from 'react';
import SweetAlert from 'sweetalert2';
import { AlertState } from '../../../Constant';
import { Col, Card, CardBody, Button } from 'reactstrap';
import { AlertSweetalertData } from '../../Common/Data/Bonus-ui';
import HeaderCard from '../../Common/Component/HeaderCard';

const Alert = () => {

    // eslint-disable-next-line
    const [alert, setalert] = useState(false)

    const Displayalert = (name) => {

        setalert(true);

        if (name === 'alertSuccess') {
            SweetAlert.fire({ title: 'Good job!', text: 'You clicked the button!', icon: 'success' });
        }
        if (name === 'alertDanger') {
            SweetAlert.fire({ title: 'Good job!', text: 'You clicked the button!', icon: 'error' });
        }
        if (name === 'alertInfo') {
            SweetAlert.fire({ title: 'Good job!', text: 'You clicked the button!', icon: 'info' });
        }
        if (name === 'alertWarning') {
            SweetAlert.fire({ title: 'Good job!', text: 'You clicked the button!', icon: 'warning' });
        }
    };

    return (
        <Fragment>
            <Col sm="12">
                <Card>
                    <HeaderCard title={AlertState} />
                    <CardBody>
                        <div className="btn-showcase">
                            {AlertSweetalertData.map((item, i) =>
                                <Button key={i} color={item.color} className={item.class} name={item.name} onClick={(e) => Displayalert(e.target.name)} >{item.title}</Button>
                            )}
                        </div>
                    </CardBody>
                </Card>
            </Col>
        </Fragment>
    );
};

export default Alert;