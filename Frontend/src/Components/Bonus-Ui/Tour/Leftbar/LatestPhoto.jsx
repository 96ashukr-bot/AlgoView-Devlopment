import React, { Fragment, useState } from 'react';
import { ChevronDown, ChevronUp } from 'react-feather';
import { Card, CardHeader, CardBody } from 'reactstrap';
import { Btn, H5, LI, UL } from '../../../../AbstractElements';
import Image from '../../../../CommonElements/Media';
import { LatestPhotosData } from '../../../Common/Data/Bonus-ui';

const LatestPhotos = ({ colClass }) => {
  const [isShow, setIsShow] = useState(true);

  const toggleClick = () => {
    setIsShow(!isShow);
  };

  return (
    <Fragment>
      <div className={colClass}>
        <Card>
          <CardHeader>
            <H5 attrH5={{ className: 'p-0' }}>
              <Btn
                attrBtn={{
                  className: 'btn btn-link d-flex justify-content-between',
                  color: 'transperant',
                  onClick: toggleClick,
                }}>
                Latest Photos {isShow ? <ChevronUp className='m-0' /> : <ChevronDown className='m-0' />}
              </Btn>
            </H5>
          </CardHeader>
          <div className={`collapse ${isShow ? 'show' : ''}`} id='collapseicon4' data-parent='#accordion' aria-labelledby='collapseicon4'>
            <CardBody className='photos filter-cards-view'>
              <UL attrUL={{ className: 'simple-list border-0 flex-row' }}>
                {LatestPhotosData.map((item) => (
                  <LI attrLI={{className:"border-0"}} key={item.id}>
                    <div className='latest-post'>
                      <Image attrImage={{ className: 'img-fluid', alt: '', src: item.img }} />
                    </div>
                  </LI>
                ))}
              </UL>
            </CardBody>
          </div>
        </Card>
      </div>
    </Fragment>
  );
};

export default LatestPhotos;
