
#include <deque>
#include "zeromq/zmq.hpp"

#include "cinder/app/AppNative.h"
#include "cinder/app/RendererGl.h"
#include "cinder/gl/Shader.h"
#include "cinder/gl/Batch.h"
#include "cinder/gl/VboMesh.h"
#include "cinder/ImageIo.h"
#include "cinder/Triangulate.h"
#include "cinder/Utilities.h"
#include "cinder/audio/Context.h"
#include "cinder/audio/SamplePlayerNode.h"
#include "cinder/audio/MonitorNode.h"
#include "cinder/audio/GainNode.h"
#include "cinder/audio/FilterNode.h"
#include "cinder/audio/InputNode.h"
#include "cinder/audio/Utilities.h"
#include <cinder/Json.h>
#include <cinder/MayaCamUI.h>
#include <cinder/Rand.h>

using namespace ci;
using namespace ci::app;

#define USE_FILE 0

class Sketch01App : public AppNative {
public:
	virtual void	setup() override;
	virtual void	resize() override;
	virtual void	update() override;
	virtual void	draw() override;
	virtual void	fileDrop( FileDropEvent event ) override;
	virtual void	keyDown( KeyEvent event ) override;
	virtual void	mouseMove( MouseEvent event ) override;
	virtual void	mouseDown( MouseEvent event ) override;
	virtual void	mouseDrag( MouseEvent event ) override;
	virtual void	prepareSettings( ci::app::AppBasic::Settings *settings ) override;

	void drawOutline( size_t lineWidth );

	MayaCamUI			mMayaCam;
	gl::BatchRef		mBatch;
	gl::GlslProgRef		mTestShader;
	audio::FilePlayerNodeRef		mFilePlayerNode;
	audio::MonitorNodeRef			mMonitorNode1;
	audio::MonitorNodeRef			mMonitorNode2;
	audio::InputDeviceNodeRef		mInputNode;
	audio::GainNodeRef				mGainNode;
	audio::FilterLowPassNodeRef		mLowpassNode;
	audio::FilterHighPassNodeRef	mHighpassNode;
	
	std::unique_ptr<zmq::context_t> mContext;
	std::unique_ptr<zmq::socket_t> mSubscriber;
	std::map<std::string, vec3> mJointMap;
	JsonTree mJsonFileNode;
	JsonTree::Iter mJsonFileIter;
	ci::AxisAlignedBox3f mPointBBox;
	bool mIsCameraInit = false;

	struct Particle
	{
		Particle() 
			: pos( 0.0f ), vel( 1.0f ), size( 10.0f ), alpha( 1.0f ), isDead( true )
		{
		}
		vec3 pos;
		vec3 vel;
		float size;
		float alpha;
		bool isDead;

	};
	std::deque<Particle> mParticles;
	ci::vec2 mMousePos;
	float mIntensity;
	bool mApplyIntensity;
};

void Sketch01App::prepareSettings( Settings* settings )
{
	settings->prepareWindow( Window::Format().size( 960, 720 ).title( "Sketch01" ) );
	settings->setFrameRate( 60.0f );
}

void Sketch01App::setup()
{
	CameraPersp cam( mMayaCam.getCamera() );
	cam.lookAt( vec3( 1000, 1000, 1000 ), vec3( 0 ) );
	cam.setCenterOfInterestPoint( vec3( 0 ) );
	mMayaCam.setCurrentCam( cam );

	mFilePlayerNode = audio::Context::master()->makeNode( new audio::FilePlayerNode() );
	mGainNode = audio::Context::master()->makeNode( new audio::GainNode( 0.5f ) );
	//mFilePlayerNode >> mGainNode >> audio::Context::master()->getOutput();
	mGainNode >> audio::Context::master()->getOutput();

	mMonitorNode1 = audio::Context::master()->makeNode( new audio::MonitorNode() );
	mMonitorNode2 = audio::Context::master()->makeNode( new audio::MonitorNode() );
	mLowpassNode = audio::Context::master()->makeNode( new audio::FilterLowPassNode() );
	mHighpassNode = audio::Context::master()->makeNode( new audio::FilterHighPassNode() );
	mInputNode = audio::Context::master()->createInputDeviceNode();

	//mInputDeviceNode >> mLowpassNode;
	//mInputDeviceNode >> mHighpassNode;

	mLowpassNode >> mMonitorNode1;
	mHighpassNode >> mMonitorNode2;

#if ( !USE_FILE )
		mContext.reset( new zmq::context_t( 1 ) );
		mSubscriber.reset( new zmq::socket_t( *mContext, ZMQ_SUB ) );
		//mSubscriber->connect( "tcp://172.31.252.124:5556" ); // Will
		mSubscriber->connect( "tcp://172.31.253.53:5556" ); // Tanner
		//mSubscriber->connect( "tcp://localhost:5563" );
		std::string stateChannel( "dancer-state" );
		mSubscriber->setsockopt( ZMQ_SUBSCRIBE, stateChannel.c_str(), stateChannel.size() );
		std::string beatChannel( "dance-beat" );
		mSubscriber->setsockopt( ZMQ_SUBSCRIBE, beatChannel.c_str(), beatChannel.size() );
		int timeout = 100;
		mSubscriber->setsockopt( ZMQ_RCVTIMEO, &timeout, sizeof( timeout ) );
#else
	mJsonFileNode = JsonTree( app::loadAsset( "sample_dancer-state.txt" ) );
	mJsonFileIter = mJsonFileNode.begin();
	mIsCameraInit = false;
#endif

	mIntensity = 1.0f;
	mApplyIntensity = false;
}

void Sketch01App::fileDrop( FileDropEvent event )
{
	fs::path filePath = event.getFile( 0 );
	getWindow()->setTitle( filePath.filename().string() );

	//audio::Context::master()->disable();
	audio::SourceFileRef sourceFile = audio::load( loadFile( filePath ) );

	mFilePlayerNode->setSourceFile( sourceFile );
	mFilePlayerNode->setLoopEnabled();
	mFilePlayerNode >> mGainNode;

	mFilePlayerNode >> mLowpassNode;
	mFilePlayerNode >> mHighpassNode;

	audio::Context::master()->enable();
	mFilePlayerNode->start();

	mLowpassNode->enable();
	//mLowpassNode->setMode();
}

void Sketch01App::resize()
{
	CameraPersp cam( mMayaCam.getCamera() );
	cam.setPerspective( 60, getWindowAspectRatio(), 1, 1000 );
	mMayaCam.setCurrentCam( cam );
}

void Sketch01App::update()
{
	bool isBeatMsg = false;
	JsonTree updateNode;
	mPointBBox = ci::AxisAlignedBox3f( vec3( FLT_MAX, FLT_MAX, FLT_MAX ), vec3( -FLT_MAX, -FLT_MAX, -FLT_MAX ) );
#if ( !USE_FILE )
	if( !mSubscriber->connected() ) {
			return;
		}
	zmq::message_t update;
	mSubscriber->recv( &update );
	std::string jsonDataStr = std::string( static_cast<char*>( update.data() ), update.size() );
	
	if( !jsonDataStr.empty() ) {
		int beatFoundPos = jsonDataStr.find( "dance-beat" );
		if( beatFoundPos != std::string::npos ) {
			isBeatMsg = true;
		}
		size_t firstBracePos = jsonDataStr.find_first_of( '{' );
		if( firstBracePos != std::string::npos ) {
			jsonDataStr = jsonDataStr.substr( firstBracePos, jsonDataStr.size() );
		}
		updateNode = JsonTree( jsonDataStr );
	}
#else
	updateNode = *mJsonFileIter;
	++mJsonFileIter;
	if( mJsonFileIter == mJsonFileNode.end() ) {
		mJsonFileIter = mJsonFileNode.begin();
	}
#endif

	{
		if( isBeatMsg ){
			if( updateNode.hasChild( "intensity" ) ) {
				//JsonTree timestampNode = updateNode.getChild( "timestamp" );
				JsonTree intensityNode = updateNode.getChild( "intensity" );
				mIntensity = intensityNode.getValue<float>();
				mApplyIntensity = true;
			}
		}
		else {
			if( updateNode.hasChild( "points" ) ) {
				//JsonTree timestampNode = updateNode.getChild( "timestamp" );
				JsonTree pointsNode = updateNode.getChild( "points" );
				for( auto ptIter = pointsNode.begin(), ptEnd = pointsNode.end(); ptIter != ptEnd; ++ptIter ) {
					const std::string key = ptIter->getKey();
					float x = ptIter->getValueAtIndex<float>( 0 );
					float y = ptIter->getValueAtIndex<float>( 1 );
					float z = ptIter->getValueAtIndex<float>( 2 );
					vec3 v = vec3( x, y, z );
					mPointBBox.include( v );
					mJointMap[key] = v;
				}
			}
		}
	}

	if( !mIsCameraInit ) {
		ci::CameraPersp cam( mMayaCam.getCamera() );
		vec3 centerPt = mPointBBox.getCenter();
		cam.lookAt( centerPt - vec3( 0.0f, 0.0f, 1800.0f ), centerPt );
		cam.setFarClip( 10000.0f );
		cam.setNearClip( 10.0f );
		cam.setFov( 80.0f );
		mMayaCam.setCurrentCam( cam );
		mIsCameraInit = true;

		mParticles.resize( 100 );
	}

	if( !mJointMap.empty() ) {
		for( auto &p : mParticles ) {
			p.pos += p.vel * ( mMousePos.y  * 0.1f );
			if( p.isDead || ( p.pos.z < 0.0f ) ) {

				int selJointIdx = randInt() % mJointMap.size();
				auto jtIter = mJointMap.begin();
				std::advance( jtIter, selJointIdx );
				p.pos = jtIter->second;
				p.vel = vec3( 0, 0, -1.0f );
				p.isDead = false;
			}// end if
		}// end for
	}// end if
}

void Sketch01App::draw()
{
	gl::clear();

	gl::pushMatrices();
	gl::setMatrices( mMayaCam.getCamera() );

	gl::color( Color::white() );
	for( auto const &jointPair : mJointMap ) {
		const vec3 &pt = jointPair.second;
		ci::gl::color( Color( 1, 1, 1 ) );
		ci::gl::drawSphere( pt, 10.0f, 12 );
	}

	for( auto const &p : mParticles ) {
		ci::gl::color( Color( 1, 0, 0 ) );
		float size = p.size;
		if( mApplyIntensity ) {
			size *= mIntensity;
		}
		ci::gl::drawSphere( p.pos, size, 12 );
	}
	mApplyIntensity = false;
	gl::popMatrices();
}

void Sketch01App::keyDown( KeyEvent event )
{
	if( event.getCode() == KeyEvent::KEY_SPACE ) {
		if( mFilePlayerNode->isEnabled() ) {
			mFilePlayerNode->stop();
		}
		else {
			mFilePlayerNode->start();
		}
	}
	else if( event.getCode() == KeyEvent::KEY_UP ) {
		if( mGainNode->isEnabled() ) {
			mGainNode->setValue( mGainNode->getValue() + 0.1f );
		}
	}
	else if( event.getCode() == KeyEvent::KEY_DOWN ) {
		if( mGainNode->isEnabled() ) {
			mGainNode->setValue( mGainNode->getValue() - 0.1f );
		}
	}
}

void Sketch01App::mouseMove( MouseEvent event )
{
	if( !getWindowBounds().contains( event.getPos() ) )
		return;
	mMousePos = event.getPos();
}

void Sketch01App::mouseDown( MouseEvent event )
{
	mMayaCam.mouseDown( event.getPos() );
}

void Sketch01App::mouseDrag( MouseEvent event )
{
	mMayaCam.mouseDrag( event.getPos(), event.isLeftDown(), event.isMiddleDown(), event.isRightDown() );
}



CINDER_APP_NATIVE( Sketch01App, RendererGl )
