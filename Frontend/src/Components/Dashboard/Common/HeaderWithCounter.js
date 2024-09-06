import React, { Fragment } from 'react';
import CountUp from 'react-countup';
import { CardHeader, Media } from 'reactstrap';
import { H4, P } from '../../../AbstractElements';

const HeaderWithCountUp = ({ title, val, countUp }) => {
    return (
        <Fragment>
            <CardHeader className="card-no-border">
                <Media>
                    <div className="media-body">
                        <P><span className="f-w-500 font-roboto">{title}</span><span className="f-w-700 font-primary ms-2">{val}</span></P>
                        <H4 attrH4={{ className: "f-w-500 mb-0 f-26 counter" }} >
                            <CountUp end={countUp} /></H4>
                    </div>
                </Media>
            </CardHeader>
        </Fragment>
    )
}

export default HeaderWithCountUp