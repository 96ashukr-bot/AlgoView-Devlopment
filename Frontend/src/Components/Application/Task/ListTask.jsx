import React, { Fragment, useRef } from 'react';
import ReactToPrint from 'react-to-print';
import { Printer } from 'react-feather';
import { Card, CardHeader } from 'reactstrap';
import { CreatedByMe, Print } from '../../../Constant';
import { H6 } from '../../../AbstractElements';
import CreatedByme from './CreatedByme';

const ListOfTask = () => {
    const componentRef = useRef();
    return (
        <Fragment>
            <Card className="mb-0">
                <CardHeader className="d-flex">
                    <H6 attrH6={{ className: 'mb-0 f-w-600' }} >{CreatedByMe}</H6>
                    <ReactToPrint
                        trigger={() => (
                            <a href="#javascript"><Printer className="me-2" />{Print}</a>
                        )}
                        content={() => componentRef.current}
                    />
                </CardHeader>
                <CreatedByme />
            </Card>
        </Fragment>
    );
};

export default ListOfTask;