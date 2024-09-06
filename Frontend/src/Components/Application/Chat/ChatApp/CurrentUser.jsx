import React, { Fragment, useContext } from 'react';
import ChatAppContext from '../../../../_helper/Chat';
import { Link } from 'react-router-dom';
import { Image } from '../../../../AbstractElements';
import CustomizerContext from '../../../../_helper/Customizer';

const CurrentUser = () => {
  const { currentUserr } = useContext(ChatAppContext);
  const { layoutURL } = useContext(CustomizerContext);
  var images = require.context('../../../../assets/images', true);
  const dynamicImage = (image) => {
    return images(`./${image}`);
  };

  return (
    <Fragment>
      {currentUserr && (
        <div className='media'>
          <Image
            attrImage={{
              src: `${dynamicImage(currentUserr.thumb)}`,
              className: 'rounded-circle user-image',
              alt: '',
            }}
          />
          <div className='about'>
            <Link to={`/app/users/profile/${layoutURL}`}>
              <div className='name f-w-600'>{currentUserr.name}</div>
            </Link>
            <div className='status'>{currentUserr.status}</div>
          </div>
        </div>
      )}
    </Fragment>
  );
};

export default CurrentUser;
