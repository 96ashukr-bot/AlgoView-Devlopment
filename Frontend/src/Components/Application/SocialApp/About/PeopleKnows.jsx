import React, { Fragment } from 'react'
import { CardBody } from 'reactstrap';
import { Btn, Image, LI, UL } from '../../../../AbstractElements';
import { AvatarsData } from '../../../../Data/SocialHeader';

const PeopleKnows = () => {
    return (
        <Fragment>
            <CardBody className="avatar-showcase">
                <div className="pepole-knows">
                    <UL attrUL={{ className: 'flex-row' }}>
                        {AvatarsData.map((item, i) => (
                            <LI attrLI={{ className: 'border-0' }} key={i}>
                                <div className="add-friend text-center">
                                    <Image attrImage={{ className: "img-60 img-fluid rounded-circle", alt: "", src: `${item.img}` }} />
                                    <span className="d-block f-w-600">{item.name}</span>
                                    <Btn attrBtn={{ color: "primary", size: "xs" }} >{item.btn}</Btn>
                                </div>
                            </LI>
                        ))}
                    </UL>
                </div>
            </CardBody>
        </Fragment>
    )
}

export default PeopleKnows;