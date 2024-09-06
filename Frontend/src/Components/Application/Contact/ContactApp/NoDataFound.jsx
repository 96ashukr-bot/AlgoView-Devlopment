import React, { Fragment } from 'react';
import { Card, CardBody } from 'reactstrap';
import { P } from '../../../../AbstractElements';
import { NoDataFound } from '../../../../Constant';
import HeaderCard from '../../../Common/Component/HeaderCard';

const NoDataFoundClass = ({ title }) => {
    return (
        <Fragment>
            <Card className="mb-0">
                <HeaderCard title={title} span1={'10 Contacts'} />
                <CardBody>
                    <P>{NoDataFound} </P>
                </CardBody>
            </Card>
        </Fragment>
    );
};

export default NoDataFoundClass;