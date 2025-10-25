#ifndef _MEMORY_GLOBAL_H_
#define _MEMORY_GLOBAL_H_

#ifdef _MSC_VER
#   pragma warning(push)
#   pragma warning(disable: 4251)
#endif

#ifdef _WIN32
#   ifdef LIBMEMORY_LIBRARY_EXPORT
#       define MEMORY_EXPORT __declspec(dllexport)
#   else
#       define MEMORY_EXPORT __declspec(dllimport)
#   endif
#elif __GNUC__ >= 4
#   define MEMORY_EXPORT __attribute__((visibility("default")))
#else
#   define MEMORY_EXPORT 
#endif

#endif