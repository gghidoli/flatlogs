#include <assert.h>
#include "../catch.hpp"
#include "generated/binarySchemata.inc"
#include "generated/logCodes.hpp"
////////////////////////////////////////////////////////////////////////
// todo:  use all other types/<log-type>.hpp files via
//            #include "generated/logTypes.hpp"
//        - this will be a problem because some of those <log-type>.hpp
//          header files depend on MagAOX repo.
//
#include "types/git_state.hpp"
////////////////////////////////////////////////////////////////////////
#include "types/generated/git_state_generated.h"
#include "types/flatbuffer_log.hpp"

const std::string gsName{"gsName"};  // Dummy GIT repo name
const std::string gsSha1{"gsSha1"};  // Dummy GIT SHA1 value string

/** Class to encapsulate GIT State flatbuffer data using
 ** => types/git_state.hpp
 ** => types/generated/git_state_generated.h
 **/
class GSM
{
public:
  std::string m_saveGsName;  // Saved input parameter value; unused
  std::string m_saveGsSha1;
  bool m_saveModified;

  std::string m_name;        // Parameters retrieved from flatbuffer
  std::string m_sha1;
  bool m_modified;

  bool m_verify{false};      // Flatbuffers verifier success/failure

  int L;                     // flatbuffer data length; used in ::verify

  // Constructor
  GSM(std::string name_, std::string sha1_, bool mod_) {
    // Save input parameters
    m_saveGsName = name_;
    m_saveGsSha1 = sha1_;
    m_saveModified = mod_;

    // Create the flatbuffer messageT using the input parameters
    auto gsm = MagAOX::logger::git_state::messageT(name_, sha1_, mod_);

    // Retrieve flatbuffer pointer and length
    void* p = gsm.builder.GetBufferPointer();
    L = MagAOX::logger::git_state::length(gsm);

    // Retrieve the flatbuffer parameters for Catch2 comparison below
    m_name = std::string(MagAOX::logger::git_state::repoName(p));
    m_sha1 = MagAOX::logger::GetGit_state_fb(p)->sha1()->c_str();
    m_modified = MagAOX::logger::GetGit_state_fb(p)->modified();

    // Run the git_state verifier
    m_verify = verify(gsm);
  }

  // Run the flatbuffer Verifier for this log type
  // - requires bufferPtrT (shared_ptr<char*>) to full log entry
  //   comprising log header plus flatbuffer log message
  bool verify(const typename MagAOX::logger::git_state::messageT& msg) {

    // Timestamp, prioriy (use nominal value here)
    flatlogs::timespecX tsx{0,0};
    flatlogs::logPrioT prio{flatlogs::logPrio::LOG_DEFAULT};

    // Create full log: log header(*); log message (+)
    // * Log level (priority)
    // * Event code (implicit in <MagAOX::logger::type>)
    // * Timestamp
    // * Message size (variable length; 1, 2, or 8 bytes)
    // + Message (variable length)

    // N.G. allocates space and writes pointer value to logBuffer
    flatlogs::bufferPtrT logBuffer;
    flatlogs::logHeader::createLog<MagAOX::logger::git_state>(logBuffer
                                                             , tsx, msg
                                                             , prio);
    // Run full log through flatbuffer Verifier
    return MagAOX::logger::git_state::verify(logBuffer,L);
  }
};

SCENARIO( "Create", "[a log item]")
{
    GIVEN("a git_state log code")
    {
        WHEN("[modified] value is true")
        {
            bool modif{true};
            // Create flatbuffer
            GSM gs(gsName, gsSha1, modif);
            // Compare flatbuffer parameters
            REQUIRE(gs.m_name == gsName);
            REQUIRE(gs.m_sha1 == gsSha1);
            REQUIRE(gs.m_modified == modif);
            REQUIRE(gs.m_verify);
        }
        WHEN("[modified] value is false")
        {
            bool modif{false};
            GSM gs(gsName, gsSha1, modif);
            REQUIRE(gs.m_name == gsName);
            REQUIRE(gs.m_sha1 == gsSha1);
            REQUIRE(gs.m_modified == modif);
            REQUIRE(gs.m_verify);
        }
    }
}
