import React, { Fragment } from 'react';
import { Image, P } from '../../../../AbstractElements';
import { NoMailFound } from '../../../../Constant';

var images = require.context('../../../../assets/images', true);

const EmptyClass = () => {
    return (
        <Fragment>
            <div className="search-not-found text-center ng-star-inserted" >
                <div className="">
                    <Image attrImage={{ alt: "", className: "second-search", src: `${images(`./search-not-found.png`)}` }} />
                    <P attrPara={{ className: "mb-0" }} >{NoMailFound}</P>
                </div>
            </div>
        </Fragment>
    )
}

export default EmptyClass