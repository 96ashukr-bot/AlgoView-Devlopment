import React, { Fragment, useCallback, useState } from 'react';
import { Row, Col, Card, CardBody, TabContent } from 'reactstrap';
import { Orgenization } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';
import NavOrg from './OrganiceTab/NavOrg';
import TabOrg from './OrganiceTab/TabOrg';

const OrgenizationTab = () => {
    const [orgactiveTab, setOrgActiveTab] = useState('1');
    const callback = useCallback((tab) => {
        setOrgActiveTab(tab);
    });

    return (
        <Fragment>
            <Card className="mb-0">
                <HeaderCard title={Orgenization} span1={'10 Contacts'} />
                <CardBody className="p-0">
                    <Row className="list-persons">
                        <NavOrg callback={callback} />
                        <Col xl="8" md="7" className='xl-50'>
                            <TabContent activeTab={orgactiveTab}>
                                <TabOrg />
                            </TabContent>
                        </Col>
                    </Row>
                </CardBody>
            </Card>
        </Fragment>
    );
};

export default OrgenizationTab;