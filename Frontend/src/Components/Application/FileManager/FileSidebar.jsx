import React, { Fragment, useState } from 'react';
import { Database, Grid } from 'react-feather';
import { Card, CardBody, Col } from 'reactstrap';
import { H5, H6, LI, P, UL, Image, Btn } from '../../../AbstractElements';
import fold from '../../../assets/images/dashboard/folder.png';
import fold1 from '../../../assets/images/dashboard/folder1.png';
import { SideButtons } from '../../Common/Data/FileManager';

const FileSideBar = () => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <Fragment>
      <Col xl='3' className='box-col-3 pe-0 file-spacing'>
        <div className='md-sidebar job-sidebar'>
          <Btn attrBtn={{ onClick: () => setIsOpen(!isOpen), color: 'primary', className: 'md-sidebar-toggle' }}>File Filter</Btn>
          <div className={`md-sidebar-aside job-left-aside custom-scrollbar ${isOpen && 'open'}`}>
            <div className='file-sidebar'>
              <Card>
                <CardBody>
                  <UL attrUL={{ className: 'simple-list ' }}>
                    {SideButtons.map((item, i) => {
                      return (
                        <LI attrLI={{ className: 'border-0' }} key={i}>
                          <div className={item.className}>
                            {item.icon}
                            {item.title}
                          </div>
                        </LI>
                      );
                    })}
                  </UL>
                  <hr />
                  <UL attrUL={{ className: 'simple-list border-0' }}>
                    <LI attrLI={{ className: 'border-0' }}>
                      <div className='btn btn-outline-primary'>
                        <Database />
                        Storage
                      </div>
                      <div className='m-t-15'>
                        <div className='progress sm-progress-bar mb-1'>
                          <div className='progress-bar bg-primary' role='progressbar' style={{ width: '25%' }} aria-valuenow='25' aria-valuemin='0' aria-valuemax='100'></div>
                        </div>
                        <P>{'25 GB of 100 GB used'}</P>
                      </div>
                    </LI>
                  </UL>
                  <hr />
                  <UL attrUL={{ className: 'simple-list' }}>
                    <LI attrLI={{ className: 'border-0' }}>
                      <div className='btn btn-outline-primary'>
                        <Grid />
                        Pricing Plan
                      </div>
                    </LI>
                    <LI attrLI={{ className: 'border-0' }}>
                      <div className='pricing-plan'>
                        <H6>Trial Version </H6>
                        <H5>FREE</H5>
                        <P>{'100 GB Space'}</P>
                        <div className='btn btn-outline-primary btn-xs'>Selected</div>
                        <Image attrImage={{ className: 'bg-img', src: `${fold}`, alt: '' }} />
                      </div>
                    </LI>
                    <LI attrLI={{ className: 'border-0' }}>
                      <div className='pricing-plan'>
                        <H6>Premium</H6>
                        <H5>{'$5/month'}</H5>
                        <P> {'200 GB Space'}</P>
                        <div className='btn btn-outline-primary btn-xs'>Contact Us</div>
                        <Image attrImage={{ className: 'bg-img', src: `${fold1}`, alt: '' }} />
                      </div>
                    </LI>
                  </UL>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </Col>
    </Fragment>
  );
};
export default FileSideBar;
