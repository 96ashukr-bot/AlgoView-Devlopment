import React, { Fragment } from 'react';
import { Media } from 'reactstrap';
import { H6, P } from '../../../../AbstractElements';

var images = require.context('../../../../assets/images', true);

const AllEmailsClass = ({ list, selectMailCallback, selectedmailCallback, checked }) => {
  const dynamicImage = (image) => {
    return images(`./${image}`);
  };

  return (
    <Fragment>
      <Media onClick={() => selectMailCallback(list)}>
        {/* <Label className="d-block" htmlFor="chk-ani">
                    <Input className="checkbox_animated"
                        name="chk-ani" type="checkbox" onChange={(e) => selectedmailCallback(e, list.id)} defaultChecked={checked} />
                </Label> */}
        <div className='media-size-email'>
          <Media body className='me-3 rounded-circle img-50' src={list.image ? dynamicImage(list.image) : ''} alt='' />
        </div>
        <Media body>
          <H6>
            {list.name}
            <small>
              <span className='digits'>({list.date})</span>
            </small>
          </H6>
          <P>{list.cc},</P>
        </Media>
      </Media>
    </Fragment>
  );
};

export default AllEmailsClass;
