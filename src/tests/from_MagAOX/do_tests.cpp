#include <assert.h>
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

////////////////////////////////////////////////////////////////////////
/// todo:  convert tests to Catch2
int
main(int argc, char** argv)
{
  std::string gsName{"gsName"};
  std::string gsSha1{"gsSha1"};

  auto gsmtrue{MagAOX::logger::git_state::messageT(gsName, gsSha1, true)};
  void* ptrue = gsmtrue.builder.GetBufferPointer();
  int Ltrue = MagAOX::logger::git_state::length(gsmtrue);

  auto gsmfalse{MagAOX::logger::git_state::messageT(gsName, gsSha1, false)};
  void* pfalse = gsmtrue.builder.GetBufferPointer();
  int Lfalse = MagAOX::logger::git_state::length(gsmfalse);

  //std::cout << L << ';' << p << std::endl;
  //std::cout << '[' << MagAOX::logger::git_state::msgString(p,L) << ']' << std::endl;

  try {
    std::string s{MagAOX::logger::git_state::repoName(ptrue)};
    if (s!=gsName) { throw(std::string("'") + s + "'!='" + gsName + "'"); }

    s = MagAOX::logger::git_state::repoName(pfalse);
    if (s!=gsName) { throw(std::string("'") + s + "'!='" + gsName + "'"); }

    s = MagAOX::logger::GetGit_state_fb(ptrue)->sha1()->c_str();
    if (s!=gsSha1) { throw(std::string("'") + s + "'!='" + gsSha1 + "'"); }

    s = MagAOX::logger::GetGit_state_fb(pfalse)->sha1()->c_str();
    if (s!=gsSha1) { throw(std::string("'") + s + "'!='" + gsSha1 + "'"); }

  } catch(std::string e) {
    std::cerr << "Failed:  [" << e << "]" << std::endl;
    return 1;
  }
  std::cerr << "Success" << std::endl;
  return 0;
}
